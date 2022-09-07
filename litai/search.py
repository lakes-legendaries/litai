"""Search Engine"""

import os
from os.path import join
from random import choices
from typing import Iterator, Union

from numpy import array
from pandas import DataFrame, read_sql_query
from sqlalchemy import create_engine


class SearchEngine:
    """Search Engine

    Parameters
    ----------
    articles_table: str, optional, default='articles'
        Name of table in :code:`database`
    connection_str: str, optional, default='litai-mysql'
        file containing connection string, in directory SECRETS_DIR (defined by
        environmental variable)
    """
    def __init__(
        self,
        /,
        articles_table: str = 'articles',
        *,
        connection_str: str = 'litai-mysql',
    ):
        # save passed
        self._articles_table = articles_table

        # load connection string
        self._connection_str = open(
            join(
                os.environ['SECRETS_DIR'],
                connection_str,
            ),
            'r',
        ).read().strip()

        # connect to db
        self._engine = create_engine(self._connection_str)

    def search(
        self,
        /,
        keywords: Union[str, list[str]] = None,
        max_date: str = None,
        min_date: str = None,
        pmids: list[Union[str, int]] = None,
        scores_table: str = None,
        *,
        join: str = 'AND',
        limit: int = 30,
        min_score: float = None,
        require_abstract: bool = True,

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
        scores_table: str, optional, default=None
            search for articles from within this table
        join: str, optional, default='AND'
            if :code:`'AND'`, require that all keywords be present in found
            articles. If :code:`'OR'`, require that any keyword be present in
            found articles.
        limit: int, optional, default=30
            max number of results
        min_score: float, optional, default=None
            minimum score to include in results. Ignored if
            :code:`scores_table` is not provided
        require_abstract: bool. optional, default=True
            only pull articles with abstracts

        Returns
        -------
        DataFrame
            Matching articles
        """

        # select cols
        query = f"""
            SELECT {
                ', '.join([
                    f'{self._articles_table}.{field}'
                    for field in [
                        'PMID',
                        'DOI',
                        'Date',
                        'Title',
                        'Abstract',
                        'Keywords',
                    ]
                ]) + (
                    f', {scores_table}.Score'
                    if scores_table
                    else ''
                )
            } FROM {self._articles_table}
        """

        # join scores table
        if scores_table:
            query += f"""
                INNER JOIN {scores_table}
                ON {scores_table}.PMID = {self._articles_table}.PMID
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
        if min_score is not None:
            query += f"""
                {'AND' if has_conditions else 'WHERE'}
                (Score >= {min_score})
            """
            has_conditions = True

        # condition: has abstract
        if require_abstract:
            query += f"""
                {'AND' if has_conditions else 'WHERE'}
                (Abstract != '')
            """
            has_conditions = True

        # order results
        if scores_table:
            query += """
                ORDER BY Score DESC
            """
        else:
            query += """
                ORDER BY _ROWID_ DESC
            """

        # limit results
        if limit:
            query += f"""
                LIMIT {limit}
            """

        # return matching articles
        return read_sql_query(query, con=self._engine)

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
        ids = self._engine.execute(
            f'SELECT PMID FROM {self._articles_table}'
        ).fetchall()
        pmids = choices(ids, k=count)
        return read_sql_query(
            f"""
            SELECT
                PMID,
                DOI,
                Date,
                Title,
                Abstract,
                Keywords
            FROM {self._articles_table}
            WHERE PMID IN {
                ", ".join([
                    f'"{pmid}"'
                    for pmid in pmids
                ])
            }
            """,
            con=self._engine,
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
            f"""
                SELECT
                    PMID,
                    DOI,
                    Date,
                    Title,
                    Abstract,
                    Keywords
                FROM {self._articles_table}
            """,
            chunksize=chunksize,
            con=self._engine,
        )

    def get_count(self) -> int:
        """Get number of articles in database

        Returns
        -------
        int
            total number of articles
        """
        query = f'SELECT COUNT(PMID) FROM {self._articles_table}'
        return self._engine.execute(query).fetchone()[0]
