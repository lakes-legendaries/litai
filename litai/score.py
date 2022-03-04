"""Score articles"""

from __future__ import annotations

from argparse import ArgumentParser
from os.path import basename, join
from random import sample
import sqlite3
from typing import Union

from numpy import array, concatenate
from pandas import concat, DataFrame, read_sql_query
import yaml

from litai.model import TokenRegressor
from litai.search import SearchEngine


class ArticleScorer(SearchEngine):
    """Score articles, spin off new database

    Parameters
    ----------
    database: str, optional, default='data/pubmed.db'
        SQL database
    table: str, optional, default='articles'
        Name of table in :code:`database`
    """

    def score(
        self,
        /,
        output_fname: str = None,
        pos_pmids: Union[str, list[Union[str, int]]] = None,
        neg_pmids: Union[str, list[Union[str, int]]] = None,
        pos_keywords: Union[list[str], str] = None,
        neg_keywords: Union[list[str], str] = None,
        *,
        downsample: int = 10000,
        exclude_passed: bool = False,
        keyword_limit: int = 3000,
        min_score: float = 0,
        rand_factor: float = 3,
        verbose: bool = True,
    ) -> DataFrame:
        """Score articles, spin off new database

        Parameters
        ----------
        output_fname: str, optional, default=None
            output database file
        pos_pmids: str or list[Union[str, int]], optional, default=None
            Target articles: Similiar articles will be scored highly. If str,
            treat as a filename
        neg_pmids: str or list[Union[str, int]], optional, default=None
            Non-target articles: Similiar articles will be scored lowly. If
            str, treat as a filename
        pos_keywords: Union[str, list[str]], optional, default=None
            pull articles with any of these keywords as positive articles
        neg_keywords: Union[str, list[str]], optional, default=None
            pull articles with any of these keywords as negative articles
        downsample: int, optional, default=10000
            If not None, then downsample df to have this max number of rows
        exclude_passed: bool, optional, default=False
            Exclude pos/neg pmids/keywords from resultant table
        min_score: float, optional, default=0
            Minimum score to be included in spinoff table
        rand_factor: float, optional, default=3
            Pull a number of random articles to include in the model, equal to
            :code:`rand_factor * (len(pos_pmids) + len(neg_pmids))`
        verbose: bool, optional, default=False
            Write running status

        Returns
        -------
        DataFrame
            Articles in new database
        """

        # load pmids from file
        if type(pos_pmids) is str:
            pos_pmids = open(pos_pmids, 'r').read().splitlines()
        if type(neg_pmids) is str:
            neg_pmids = open(neg_pmids, 'r').read().splitlines()

        # save passed
        self._output_fname = output_fname
        self._pos_pmids = pos_pmids
        self._neg_pmids = neg_pmids
        self._pos_keywords = pos_keywords
        self._neg_keywords = neg_keywords
        self._downsample = downsample
        self._exclude_passed = exclude_passed
        self._keyword_limit = keyword_limit
        self._min_score = min_score
        self._rand_factor = rand_factor
        self._verbose = verbose

        # execute jobs
        self._fit_model()
        self._score_articles()
        return self._make_new_db()

    def _fit_model(self):
        """Fit model for scoring articles"""

        # create pos / neg dfs
        pn_dfs = [
            concat((
                self.search(
                    pmids=getattr(self, f'_{sign}_pmids'),
                    limit=None,
                )
                if getattr(self, f'_{sign}_pmids') is not None
                else DataFrame(),
                self.search(
                    keywords=getattr(self, f'_{sign}_keywords'),
                    join='OR',
                    limit=self._keyword_limit,
                )
                if getattr(self, f'_{sign}_keywords') is not None
                else DataFrame(),
            ))
            for sign in ['pos', 'neg']
        ]

        # pull random articles
        rand_df = self.get_rand(int(
            self._rand_factor
            * (pn_dfs[0].shape[0] + pn_dfs[1].shape[0])
        ))

        # make labels
        pos_labels = [1] * pn_dfs[0].shape[0]
        neg_labels = [0] * pn_dfs[1].shape[0]
        rand_labels = [-1] * rand_df.shape[0]

        # format
        df = concat((pn_dfs[0], pn_dfs[1], rand_df))
        labels = concatenate((pos_labels, neg_labels, rand_labels))

        # downsample
        if self._downsample and self._downsample < df.shape[0]:
            keep_me = sample(range(df.shape[0]), self._downsample)
            df = df.iloc[keep_me, :]
            labels = labels[keep_me]

        # write running status
        if self._verbose:
            print(f'Training on {df.shape[0]} articles')

        # fit model
        self._model = TokenRegressor().fit(df, labels)

    def _score_articles(self):
        """Score all articles in table"""

        # create table
        self._con.execute('DROP TABLE IF EXISTS SCORES_TABLE')
        self._con.execute("""
            CREATE TEMPORARY TABLE SCORES_TABLE (
                PMID str,
                Score FLOAT
            )
        """)

        # score articles
        count = 0
        total = self.get_count()
        for df in self.get_all():

            # get scores
            scores = self._model.predict(df)

            # add to table
            score_str = ', '.join([
                f'({pmid}, {score})'
                for pmid, score in zip(df['PMID'], scores)
                if self._min_score is None or score >= self._min_score
            ])
            if score_str:
                self._con.execute(f"""
                    INSERT INTO SCORES_TABLE (PMID, Score)
                    VALUES {score_str}
                """)

            # write running status
            if self._verbose:
                count += df.shape[0]
                kcount = int(count / 1000)
                ktotal = int(total / 1000)
                print(f'Scored {kcount}k / {ktotal}k articles   ')

        # add linebreak at end of processing
        if self._verbose:
            print('')

    def _make_new_db(self) -> DataFrame:
        """Spin off table as new database

        Returns
        -------
        DataFrame
            Articles in new database
        """

        # create basic query
        query = f"""
            SELECT
                {self._table}.PMID,
                {self._table}.Date,
                {self._table}.Title,
                {self._table}.Abstract,
                {self._table}.Keywords,
                SCORES_TABLE.Score
            FROM {self._table}
            INNER JOIN SCORES_TABLE
            ON SCORES_TABLE.PMID = {self._table}.PMID
        """

        # exclude passed articles and keywords
        if self._exclude_passed:
            has_conditions = False
            for sign in ['pos', 'neg']:

                # exclude pmids
                pmids = getattr(self, f'_{sign}_pmids')
                if pmids:
                    query += f"""
                        {'AND' if has_conditions else 'WHERE'}
                        {self._table}.PMID NOT IN ({
                            ", ".join([
                                f'"{pmid}"'
                                for pmid in pmids
                            ])
                        })
                    """
                    has_conditions = True

                # exclude keywords
                keywords = getattr(self, f'_{sign}_keywords')
                if keywords:
                    for keyword in keywords:
                        query += f"""
                            {'AND' if has_conditions else 'WHERE'}
                            ({' AND '.join(array([
                                    [
                                        f'{field} NOT LIKE "%{keyword}%"'
                                    ]
                                    for field in [
                                        'title',
                                        'abstract',
                                        'keywords',
                                    ]
                                ]).flatten())
                            })
                        """
                        has_conditions = True

        # order by score
        query += """
            ORDER BY SCORES_TABLE.Score DESC
        """

        # extract data for new db
        df = read_sql_query(query, con=self._con)

        # dump df into new database
        if self._output_fname:
            df.to_sql(
                name=self._table,
                chunksize=1000,
                con=sqlite3.connect(self._output_fname),
                if_exists='replace',
                index=False,
            )

        # return result
        return df


# command-line interface
if __name__ == '__main__':

    # parse command line
    parser = ArgumentParser(
        description='Score articles, spin off new database',
    )
    parser.add_argument(
        'config',
        help='Configuration File'
    )
    args = parser.parse_args()

    # read config from file
    config = yaml.safe_load(open(args.config, 'r'))

    # auto-deduce output fname
    config['output_fname'] = \
        join('data', basename(args.config).split('.')[0] + '.db')

    # run article scorer
    ArticleScorer().score(**config)
