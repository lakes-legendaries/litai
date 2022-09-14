"""Score articles"""

from __future__ import annotations

from argparse import ArgumentParser
from random import sample
from typing import Union

from numpy import concatenate
from pandas import concat, DataFrame
import yaml

from litai.model import TokenRegressor
from litai.search import SearchEngine


class ArticleScorer(SearchEngine):
    """Score articles, spin off new database

    Parameters
    ----------
    articles_table: str, optional, default='articles'
        Name of table in :code:`database`
    connection_str: str, optional, default='litai-mysql'
        file containing connection string, in directory SECRETS_DIR (defined by
        environmental variable)
    """

    def score(
        self,
        /,
        config: dict[str, dict[str, Union[str, list]]],
        *,
        downsample: int = 3000,
        keyword_limit: int = 3000,
        min_score: float = 0,
        rand_factor: float = 3,
        verbose: bool = True,
    ):
        """Score articles, spin off new database

        Parameters
        ----------
        config: dict[str, dict[str, Union[str, list]]]
            Configurations to run, of the form

            .. code-block:: python

               config: {
                   scores_table_0: {
                       pos_pmids: Union[str, list[Union[str, int]]] = None,
                       neg_pmids: Union[str, list[Union[str, int]]] = None,
                       pos_keywords: Union[list[str], str] = None,
                       neg_keywords: Union[list[str], str] = None,
                   }
                   scores_table_1: {
                       ...
                   }
                   ...

            where:

            .. code-block:: numpy

               scores_table_n: str
                   name of the table to save scores into
               pos_pmids: str or list[Union[str, int]], optional, default=None
                   PMIDs for target articles: Similiar articles will be scored
                   highly. If str, treat as a filename
               neg_pmids: str or list[Union[str, int]], optional, default=None
                   PMIDs for non-target articles: Similiar articles will be
                   scored lowly. If str, treat as a filename
               pos_keywords: Union[str, list[str]], optional, default=None
                   pull articles with any of these keywords as positive
                   articles
               neg_keywords: Union[str, list[str]], optional, default=None
                   pull articles with any of these keywords as negative
                   articles

        downsample: int, optional, default=3000
            If not None, then downsample df to have this max number of rows
        keyword_limit: int, optional, default=3000
            Max number of keyword articles to pull
        min_score: float, optional, default=0
            Minimum score to be included in spinoff table
        rand_factor: float, optional, default=3
            Pull a number of random articles to include in each model, equal to
            :code:`rand_factor * (len(pos_pmids) + len(neg_pmids))`
        verbose: bool, optional, default=False
            Write running status
        """

        # save passed
        self._downsample = downsample
        self._keyword_limit = keyword_limit
        self._min_score = min_score
        self._rand_factor = rand_factor
        self._verbose = verbose

        # train models
        models = [
            self._fit_model(c)
            for c in config.values()
        ]

        # score articles
        self._score_articles(list(config.keys()), models)

    def _fit_model(
        self,
        config: dict[str, Union[str, list]],
        /,
    ) -> TokenRegressor:
        """Fit model for scoring articles

        Parameters
        ----------
        config: dict[str, Union[str, list]]
            configuration for any one individual scores table (i.e. one
            :code:`values()` from :meth:`score`'s :code:`config`).

        Returns
        -------
        TokenRegressor
            Trained model
        """

        # unpack values, with 0-index as positive, and 1-index as negative
        pmids = [config.get('pos_pmids'), config.get('neg_pmids')]
        keywords = [config.get('pos_keywords'), config.get('neg_keywords')]

        # load pmids from file
        pmids = [
            open(p, 'r').read().splitlines()
            if type(p) is str
            else p
            for p in pmids
        ]

        # create pos / neg dfs
        pn_dfs = [
            concat((
                self.search(
                    pmids=p,
                    limit=None,
                )
                if p
                else DataFrame(),
                self.search(
                    keywords=k,
                    join='OR',
                    limit=self._keyword_limit,
                )
                if k
                else DataFrame(),
            ))
            for p, k in zip(pmids, keywords)
        ]

        # pull random articles
        if self._rand_factor:
            rand_df = self.get_rand(int(
                self._rand_factor
                * (pn_dfs[0].shape[0] + pn_dfs[1].shape[0])
            ))
        else:
            rand_df = DataFrame([], columns=pn_dfs[0].columns)

        # make labels
        pos_labels = [2] * pn_dfs[0].shape[0]
        neg_labels = [1] * pn_dfs[1].shape[0]
        rand_labels = [0] * rand_df.shape[0]

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

        # return trained model
        return TokenRegressor().fit(df, labels)

    def _score_articles(
        self,
        /,
        scores_tables: list[str],
        models: list[TokenRegressor],
    ):
        """Score all articles in table

        Parameters
        ----------
        scores_tables: list[str[
            names of tables to save scores into
        models: list[TokenRegressor]
            trained models to use to score articles
        """

        # create temporary tables
        temp_tables = [
            f'{scores_table}_temp'
            for scores_table in scores_tables
        ]
        for temp_table in temp_tables:
            self._engine.execute(f'DROP TABLE IF EXISTS {temp_table}')
            self._engine.execute(f"""
                CREATE TABLE {temp_table} (
                    _ROWID_ INT NOT NULL AUTO_INCREMENT,
                    PMID INT NOT NULL,
                    Score FLOAT NOT NULL,
                    PRIMARY KEY(_ROWID_),
                    KEY(PMID),
                    KEY(Score)
                )
            """)

        # score articles
        count = 0
        total = self.get_count()
        for df in self.get_all():
            for temp_table, model in zip(temp_tables, models):

                # get scores
                scores = model.predict(df)

                # add to table
                scores_str = ', '.join([
                    f'({pmid}, {score})'
                    for pmid, score in zip(df['PMID'], scores)
                    if self._min_score is None or score >= self._min_score
                ])
                if scores_str:
                    self._engine.execute(f"""
                        INSERT INTO {temp_table} (PMID, Score)
                        VALUES {scores_str}
                    """)

            # write running status
            if self._verbose:
                count += df.shape[0]
                print(f'Scored {count:,} / {total:,} articles')

        # move from temp tables to std tables
        for temp_table, scores_table in zip(temp_tables, scores_tables):
            self._engine.execute(f'DROP TABLE IF EXISTS {scores_table}')
            self._engine.execute(
                f'RENAME TABLE {temp_table} TO {scores_table}'
            )


# command-line interface
if __name__ == '__main__':

    # parse command line
    parser = ArgumentParser(
        description='Score articles',
    )
    parser.add_argument(
        '--config',
        default='config/std.yaml',
        help='Configuration File',
    )
    args = parser.parse_args()

    # read config from file
    config = yaml.safe_load(open(args.config, 'r'))

    # run article scorer
    ArticleScorer().score(config)
