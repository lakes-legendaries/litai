from typing import Optional

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from litai.search import SearchEngine


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
        "Prompt": "Welcome to LitAI!",
        "Version": "0.1.29",
    }


@app.get("/search/")
def search(
    keywords: Optional[str] = None,
    max_date: Optional[str] = None,
    min_date: Optional[str] = None,
    scores_table: Optional[str] = None,
):
    articles = SearchEngine('data/pubmed.db').search(
        keywords=keywords.split() if keywords else None,
        max_date=max_date,
        min_date=min_date,
        scores_table=scores_table,
    )
    return {
        n: {
            'PMID': article['PMID'],
            'Title': article['Title'],
            'Abstract': article['Abstract'],
            'Date': article['Date'],
            'Score': article['Score'],
        }
        for n, article in articles.iterrows()
    }
