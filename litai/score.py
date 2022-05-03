"""Score articles"""

from __future__ import annotations

from argparse import ArgumentParser
from os.path import basename
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
    database: str, optional, default='data/pubmed.db'
        SQL database
    articles_table: str, optional, default='articles'
        Name of table in :code:`database`
    """

    def score(
        self,
        /,
        scores_table: str = None,
        pos_pmids: Union[str, list[Union[str, int]]] = None,
        neg_pmids: Union[str, list[Union[str, int]]] = None,
        pos_keywords: Union[list[str], str] = None,
        neg_keywords: Union[list[str], str] = None,
        *,
        downsample: int = 10000,
        keyword_limit: int = 3000,
        min_score: float = 0,
        rand_factor: float = 3,
        verbose: bool = True,
    ):
        """Score articles, spin off new database

        Parameters
        ----------
        scores_table: str, optional, default=None
            table to save scores into. If None, then a temporary table will be
            used.
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
        scores_table: str
        downsample: int, optional, default=10000
            If not None, then downsample df to have this max number of rows
        min_score: float, optional, default=0
            Minimum score to be included in spinoff table
        rand_factor: float, optional, default=3
            Pull a number of random articles to include in the model, equal to
            :code:`rand_factor * (len(pos_pmids) + len(neg_pmids))`
        verbose: bool, optional, default=False
            Write running status
        """

        # load pmids from file
        if type(pos_pmids) is str:
            pos_pmids = open(pos_pmids, 'r').read().splitlines()
        if type(neg_pmids) is str:
            neg_pmids = open(neg_pmids, 'r').read().splitlines()

        # save passed
        self._pos_pmids = pos_pmids
        self._neg_pmids = neg_pmids
        self._pos_keywords = pos_keywords
        self._neg_keywords = neg_keywords
        self._downsample = downsample
        self._keyword_limit = keyword_limit
        self._min_score = min_score
        self._rand_factor = rand_factor
        self._verbose = verbose

        # determine whether we're saving scores or using a temporary table
        self._temp_str = 'TEMPORARY' if not scores_table else ''
        self._scores_table = scores_table if scores_table else 'SCORES_TABLE'

        # execute jobs
        self._fit_model()
        self._score_articles()

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
        self._con.execute(f'DROP TABLE IF EXISTS {self._scores_table}')
        self._con.execute(f"""
            CREATE {self._temp_str} TABLE {self._scores_table} (
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
                    INSERT INTO {self._scores_table} (PMID, Score)
                    VALUES {score_str}
                """)

            # write running status
            if self._verbose:
                count += df.shape[0]
                kcount = int(count / 1000)
                ktotal = int(total / 1000)
                print(f'Scored {kcount}k / {ktotal}k articles', end='\r')

        # newline
        print('')

        # create indices
        for col in ['PMID', 'Score']:
            self._con.execute(f"""
                CREATE INDEX IF NOT EXISTS {self._scores_table}_{col}
                ON {self._scores_table}({col})
            """)

        # commit changes
        if not self._temp_str:
            self._con.commit()


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

    # auto-deduce name of scores table
    config['scores_table'] = basename(args.config).split('.')[0]

    # run article scorer
    ArticleScorer().score(**config)
