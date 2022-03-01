"""Search Engine"""
import sqlite3
from typing import Iterator, Union

from numpy import array
from pandas import DataFrame, read_sql_query


class SearchEngine:
    """Search Engine

    Parameters
    ----------
    database: str, optional, default='data/pubmed.db'
        SQL database
    table: str, optional, default='articles'
        Name of table in :code:`database`
    """
    def __init__(
        self,
        /,
        database: str = 'data/pubmed.db',
        table: str = 'articles',
    ):
        # save passed
        self._table = table

        # connect to database
        self._database = database
        self._con = sqlite3.connect(database)

    def search(
        self,
        /,
        keywords: Union[str, list[str]] = None,
        max_date: str = None,
        min_date: str = None,
        pmids: list[Union[str, int]] = None,
        *,
        join: str = 'AND',
        limit: int = 30,
        min_score: float = None,

    ) -> DataFrame:
        """Find article by keyword

        Parameters
        ----------
        keywords: Union[str, list[str]], optional, default=None
            keyword or keywords to use in search
        max_date: str, optional, default=None
            maximum date of articles to return
        min_date: str, optional, default=None
            minimum date of articles to return
        pmids: list[Union[str, int]], optional, default=None
            pubmed ids of articles to return
        join: str, optional, default='AND'
            if :code:`'AND'`, require that all keywords be present in found
            articles. If :code:`'OR'`, require that any keyword be present in
            found articles.
        limit: int, optional, default=30
            max number of results
        min_score: float, optional, default=0
            minimum score to include in results

        Returns
        -------
        DataFrame
            Matching articles
        """

        # check for scores column
        has_scores = 'Score' in read_sql_query(
            """
                SELECT * FROM ARTICLES
                LIMIT 1
            """,
            con=self._con,
        ).columns

        # select cols
        query = f"""
            SELECT {
                ', '.join(['PMID', 'Date', 'Title', 'Abstract', 'Keywords'
            ])} FROM {self._table}
        """

        # track if conditions have been inserted into query
        has_conditions = False

        # condition: keyword
        if keywords:
            if type(keywords) is str:
                keywords = [keywords]
            for keyword in keywords:
                query += f"""
                    {join if has_conditions else 'WHERE ('}
                    ({' OR '.join(array([
                            [
                                f'{field} LIKE "%{keyword}%"'
                            ]
                            for field in [
                                'Title',
                                'Abstract',
                                'Keywords',
                            ]
                        ]).flatten())
                    })
                """
                has_conditions = True
            query += ') '

        # condition: min_date
        if min_date:
            query += f"""
                {'AND' if has_conditions else 'WHERE'}
                (
                    Date >= "{min_date}"
                )
            """
            has_conditions = True

        # condition: max_date
        if max_date:
            query += f"""
                {'AND' if has_conditions else 'WHERE'}
                (
                    Date <= "{max_date}"
                )
            """
            has_conditions = True

        # condition: pmid
        if pmids:
            query += f"""
                {'AND' if has_conditions else 'WHERE'}
                (
                    PMID in ({
                        ", ".join([
                            f'"{pmid}"'
                            for pmid in pmids
                        ])
                    })
                )
            """
            has_conditions = True

        # condition: min_score
        if has_scores and min_score is not None:
            query += f"""
                {'AND' if has_conditions else 'WHERE'}
                (Score >= {min_score})
            """
            has_conditions = True

        # order results
        if has_scores:
            query += """
                ORDER BY Score DESC
            """
        else:
            query += """
                ORDER BY RANDOM()
            """

        # limit results
        if limit:
            query += f"""
                LIMIT {limit}
            """

        # return matching articles
        return read_sql_query(query, con=self._con)

    def get_rand(self, /, count: int) -> DataFrame:
        """Find random articles

        Parameters
        ----------
        count: int
            number of articles to pull

        Returns
        -------
        DataFrame
            Articles
        """
        return read_sql_query(
            f"""
            SELECT * FROM {self._table}
            ORDER BY RANDOM()
            LIMIT {count}
            """,
            con=self._con,
        )

    def get_all(self, /, chunksize: int = 10000) -> Iterator[DataFrame]:
        """Get all articles

        Parameters
        ----------
        chunksize: int, optional, default=10E3
            number of articles in each iteration pt of output

        Returns
        -------
        Iterator[DataFrame]
            Iterator to all articles in database
        """
        return read_sql_query(
            f'SELECT * FROM {self._table}',
            chunksize=chunksize,
            con=self._con,
        )

    def get_count(self) -> int:
        """Get number of articles in database

        Returns
        -------
        int
            total number of articles
        """
        query = f'SELECT COUNT(*) FROM {self._table}'
        return self._con.execute(query).fetchone()[0]
