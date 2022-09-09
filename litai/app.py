from typing import Optional

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from litai.search import SearchEngine
from litai._version import __version__


# create app
app = FastAPI()

# allow cors access
app.add_middleware(
    CORSMiddleware,
    allow_headers=["*"],
    allow_methods=["*"],
    allow_origins=["*"],
)


@app.get("/")
def home():
    return {
        "Package": "LitAI",
        "Version": __version__,
        "Author": "Mike Powell PhD",
        "Email": "mike@lakeslegendaries.com",
    }


@app.get("/search/")
def search(
    keywords: Optional[str] = None,
    max_date: Optional[str] = None,
    min_date: Optional[str] = None,
    scores_table: Optional[str] = None,
):
    articles = SearchEngine().search(
        keywords=keywords.split() if keywords else None,
        max_date=max_date,
        min_date=min_date,
        scores_table=scores_table,
    )
    return {
        n: {
            'PMID': article['PMID'],
            'DOI': article['DOI'],
            'Title': article['Title'],
            'Abstract': article['Abstract'],
            'Date': article['Date'],
            'Score': article['Score'],
        }
        for n, article in articles.iterrows()
    }


@app.get('/comment/')
def comment(
    pmid: str,
    token: str,
    user: str,
    comment: str,
    scores_table: Optional[str] = None,
):
    SearchEngine()._engine.execute(f"""
        INSERT INTO comments (
            Date,
            PMID,
            Token,
            User,
            {'ScoresTable,' if scores_table else ''}
            Comment
        ) VALUES (
            NOW(),
            {pmid},
            {token},
            {user},
            {scores_table + ',' if scores_table else ''}
            {comment}
        )
    """)


@app.get('/feedback/')
def feedback(
    pmid: str,
    token: str,
    user: str,
    scores_table: str,
    feedback: float,
):
    SearchEngine()._engine.execute(f"""
        INSERT INTO feedback (
            Date,
            PMID,
            Token,
            User,
            ScoresTable,
            Feedback
        ) VALUES (
            NOW(),
            {pmid},
            {token},
            {user},
            {scores_table},
            {feedback}
        )
    """)
