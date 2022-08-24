from datetime import datetime
import os
from os import remove
from os.path import join
from subprocess import run
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


@app.get("/feedback/{action}")
def feedback(
    action: str,
    pmid: Optional[str] = None,
    table: Optional[str] = None,
    token: Optional[str] = None,
):
    # validate token
    validated_tokens = open(
        join(os.environ['SECRETS_DIR'], 'litai-users'),
        'r',
    ).read().splitlines()
    if token not in validated_tokens:
        return {'Status': 'Invalid Token'}

    # write feedback to file
    fname = datetime().now().isoformat()
    with open(fname, 'w') as file:
        print(f'action: {action}', file=file)
        print(f'pmid: {pmid}', file=file)
        print(f'table: {table}', file=file)
        print(f'token: {token}', file=file)

    # upload to azure
    run(
        [
            'az',
            'storage',
            'blob',
            'upload',
            '-f',
            fname,
            '-c',
            'feedback',
            '-n',
            fname,
        ],
        capture_output=True,
        check=True,
    )

    # clean-up
    remove(fname)

    # return success
    return {'Status': 'Success'}
