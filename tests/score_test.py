from numpy import array

from litai import ArticleScorer


def test_scoring():
    df = ArticleScorer(database='data/example.db').score(
        pos_keywords='mouse',
        neg_keywords='fish',
        min_score=None,
        rand_factor=0,
    )
    terms = ['mouse', 'fish', 'mice', 'water']
    has_term = [
        array([
            df[field].str.contains(term).to_numpy()
            for field in ['Title', 'Abstract', 'Keywords']
        ]).any(axis=0)
        for term in terms
    ]
    term_scores = [
        df['Score'][included].mean()
        for included in has_term
    ]
    assert(term_scores[0] >= 0.9)
    assert(term_scores[1] <= 0.1)
    assert(term_scores[2] >= 0.5)
    assert(term_scores[3] <= 0.5)
