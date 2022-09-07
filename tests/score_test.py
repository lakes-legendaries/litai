from numpy import array
from retry import retry

from litai import ArticleScorer


def test_scoring():
    @retry(tries=10)
    def score_fun():
        scorer = ArticleScorer('pytest')
        scorer.score(
            scores_table='mouse',
            pos_keywords='mouse',
            neg_keywords='fish',
            min_score=None,
            rand_factor=0,
        )
        df = scorer.search(scores_table='mouse', min_score=1, limit=1000)
        term_freq = [
            array([
                df[field].str.contains(term).to_numpy()
                for field in ['Title', 'Abstract', 'Keywords']
            ]).any(axis=0).mean()
            for term in ['mouse', 'fish', 'mice', 'water']
        ]
        assert (term_freq[0] >= 0.5)
        assert (term_freq[1] <= 0.1)
        assert (term_freq[2] >= 0.25)
        assert (term_freq[3] <= 0.1)
    score_fun()
