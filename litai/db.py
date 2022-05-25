"""Mirror PubMed database to a local SQL database"""

from argparse import ArgumentParser
from datetime import datetime
from os import remove
from os.path import basename, isfile
import re
import sqlite3
from subprocess import run
from typing import Union

from pandas import DataFrame
from retry import retry


class DataBase:
    """Mirror PubMed database to a local SQL database

    Parameters
    ----------
    database: str, optional, default='data/pubmed.db'
        SQL database
    file_list: Union[str, list[str]], optional, default='data/file_list.txt'
        List of pubmed baseline and daily update files. If str, interpret as a
        file containing a list of the pubmed files; if list[str], interpret as
        a the list of pubmed files
    start_year: int, optional, default=2017
        First year to mirror into database
    articles_table: str, optional, default='articles'
        Name of table in :code:`database`
    """
    def __init__(
        self,
        /,
        *,
        database: str = 'data/pubmed.db',
        file_list: Union[str, list[str]] = 'data/file_list.txt',
        start_year: int = 2010,
        articles_table: str = 'articles',
    ):

        # load file list
        if type(file_list) is str:
            file_list = open(file_list, 'r').read().splitlines()

        # save passed + cols
        self._database = database
        self._file_list = file_list
        self._start_year = start_year
        self._articles_table = articles_table

    def create(self, /):
        """Create database, deleting existing"""

        # remove existing database
        if isfile(self._database):
            remove(self._database)

        # create database
        self._insert()

    def append(self, /):
        """Append to existing database, create if DNE"""

        # check that database exists
        if not isfile(self._database):
            self.create()
            return

        # get files already in db
        already_in = [
            row[0]
            for row in sqlite3.connect(self._database).execute("""
                SELECT FILE from FILES
            """).fetchall()
        ]

        # get files to be added
        self._file_list = [
            file
            for file in set(self._file_list).difference(set(already_in))
        ]

        # stop, if no files to be added
        if len(self._file_list) == 0:
            return

        # append to database
        self._insert()

    def _insert(self, /):
        """Insert articles into table"""

        # process files
        total = len(self._file_list)
        for n, server_file in enumerate(sorted(self._file_list)):

            # pull file from server
            local_file = self.__class__._get_file(server_file)

            # extract data from file
            self._extract_data(local_file).to_sql(
                name=self._articles_table,
                chunksize=1000,
                con=sqlite3.connect(self._database),
                if_exists='append',
                index=False,
            )

            # write status
            count = sqlite3.connect(self._database) \
                .execute('SELECT MAX(_ROWID_) FROM ARTICLES LIMIT 1') \
                .fetchone()[0]
            print(f'{count} articles from {n+1} / {total} files', end='\r')

            # clean up
            remove(local_file)

        # newline
        print('')

        # connect to db
        engine = sqlite3.connect(self._database)

        # remove repeated entries
        engine.execute("""
            DELETE FROM ARTICLES
            WHERE _ROWID_ NOT IN (
                SELECT MIN(_ROWID_) FROM ARTICLES
                GROUP BY PMID
            )
        """)
        engine.commit()
        engine.execute("""VACUUM""")

        # save files used to make table
        engine.execute("""
            CREATE TABLE IF NOT EXISTS FILES (
                FILE TEXT
            )
        """)
        engine.execute(f"""
            INSERT INTO FILES
            VALUES {', '.join([
                f'("{file}")'
                for file in self._file_list
            ])}
        """)

        # make indices
        for col in ['PMID', 'Date', 'Title']:
            engine.execute(f"""
                CREATE INDEX IF NOT EXISTS ARTICLES_{col}
                ON ARTICLES({col})
            """)

        # save
        engine.commit()

    @classmethod
    @retry(tries=60, delay=10)
    def _get_file(cls, server_file: str) -> str:
        """Download file from server, and extract

        Parameters
        ----------
        server_file: str
            Name of file on server

        Returns
        -------
        str
            local filename

        Raises
        ------
        CalledProcessError
            If :code:`server_file` is unable to be downloaded
        """

        # get filenames
        local_file = basename(server_file)
        unzipped_file = local_file[0:-3]

        # make sure local files DNE
        for file in [local_file, unzipped_file]:
            if isfile(file):
                remove(file)

        # pull file from server
        run(['wget', server_file], check=True, capture_output=True)

        # unzip file
        run(['gzip', '-d', local_file])

        # return local filename
        return unzipped_file

    def _extract_data(
        self,
        xml_file: str,
        *,
        year_differential: int = 5,
    ) -> DataFrame:
        """Extract structured data from xml file

        Parameters
        ----------
        xml_file: str
            xml file
        year_differential: int, optional, default=10
            Only keep articles if their first date in the system is >=
            self._start_date + year_differential. This stops us from including
            articles that are very old, but were just published online
            recently.

        Returns
        -------
        DataFrame
            Extracted data, containing:

            #. PMID
            #. Date
            #. Title
            #. Abstract
            #. Keywords
        """

        # check if file contains recent data
        with open(xml_file, 'r') as file:

            # read file
            data = file.read()

            # check for articles in recent years
            recent = False
            for year in range(self._start_year, datetime.now().year+1):
                if f'<Year>{year}</Year>' in data:
                    recent = True
                    break

            # return empty if no recent articles
            if not recent:
                return DataFrame()

        # define date parsing strings
        formats = [
            r'%Y-%m-%d',
            r'%Y-%b',
            r'%Y-%b-%d',
            r'%Y-%B',
            r'%Y-%B-%d',
        ]

        # get shorthand for regex fun
        regex = self.__class__._regex

        # initialize data dictionary and fields
        data = []
        in_pub_date = False
        pmid = date = title = abstract = keywords = ''

        # run through file
        with open(xml_file, 'r') as file:

            # skip header
            while file.readline().strip() != '<PubmedArticle>':
                pass

            # run through article
            while (line := file.readline().strip()):

                # extract pmid
                if len(pmid) == 0:
                    if match := regex(line, 'PMID'):
                        pmid = match

                # extract date
                elif line.strip() == r'<PubDate>':
                    in_pub_date = True
                    partial_date = ''
                elif in_pub_date and (match := regex(line, 'Year')):
                    partial_date = match
                elif in_pub_date and (match := regex(line, 'Month')):
                    partial_date += '-' + match
                elif in_pub_date and (match := regex(line, 'Day')):
                    partial_date += '-' + match
                elif line.strip() == r'</PubDate>':
                    in_pub_date = False

                    # format date
                    correctly_formatted = False
                    for format in formats:
                        try:
                            dtime = datetime.strptime(partial_date, format)
                            partial_date = dtime.strftime(formats[0])
                            correctly_formatted = True
                            break
                        except ValueError:
                            continue

                    # skip, if improperly formatted
                    if not correctly_formatted:
                        continue

                    # save date
                    date = partial_date

                # extract title
                elif match := regex(line, 'ArticleTitle'):
                    title = match

                # extract abstract
                elif match := regex(line, 'AbstractText'):
                    abstract = match

                # extract keywords
                elif match := regex(line, 'Keyword'):
                    if len(keywords):
                        keywords += ' '
                    keywords += match

                # end of article: save data
                elif line == '</PubmedArticle>':

                    # check if is a recent article
                    recent = date and int(date[0:4]) >= self._start_year

                    # save
                    if pmid and title and recent:
                        data.append([
                            pmid,
                            date,
                            title,
                            abstract,
                            keywords,
                        ])

                    # reset fields for next article
                    in_pub_date = False
                    pmid = date = title = abstract = keywords = ''

            # return as df
            cols = ['PMID', 'Date', 'Title', 'Abstract', 'Keywords']
            return DataFrame(data, columns=cols)

    @classmethod
    def _regex(cls, line: str, xml_field: str) -> str:
        """Extract xml_field from line

        Parameters
        ----------
        line: str
            line to parse
        xml_field: str
            xml field to extract

        Returns
        -------
        str
            value of field, or :code:`''`, if field not found
        """
        pattern = f'<{xml_field}[^>]*>(.*)</{xml_field}>'
        match = re.findall(pattern, line)
        if len(match) == 0:
            return ''
        return match[0]


# command-line interface
if __name__ == '__main__':

    # read command line
    parser = ArgumentParser(
        description='Create or append to local PubMed Database'
    )
    parser.add_argument(
        '--append',
        required=False,
        action='store_true',
        help='Append to existing database'
    )
    parser.add_argument(
        '--create',
        required=False,
        action='store_true',
        help='Create new database, deleting existing'
    )
    args = parser.parse_args()

    # check which function to run
    if args.append == args.create:
        raise ValueError('You must specify --append or --create')
    fun = DataBase.append if args.append else DataBase.create

    # run
    fun(DataBase())
