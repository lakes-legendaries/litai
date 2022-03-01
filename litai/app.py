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
        "Version": "Alpha Testing",
    }


@app.get("/search/{database}")
def search(
    database: str,
    keywords: Optional[str] = None,
    max_date: Optional[str] = None,
    min_date: Optional[str] = None,
):
    articles = SearchEngine(f'data/{database}.db').search(
        keywords=keywords.split() if keywords else None,
        max_date=max_date,
        min_date=min_date,
    )
    return {
        n: {
            'PMID': pmid,
            'Title': title,
            'Abstract': abstract,
        }
        for n, (pmid, title, abstract) in enumerate(zip(
            articles['PMID'],
            articles['Title'],
            articles['Abstract'],
        ))
    }
