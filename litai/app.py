from datetime import datetime
import os
from os import remove
from os.path import isfile, join
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
        "Package": "LitAI",
        "Version": "0.1.33",
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
    articles = SearchEngine('data/pubmed.db').search(
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


@app.get("/feedback/{action}")
def feedback(
    action: str,
    pmid: Optional[str] = None,
    table: Optional[str] = None,
    token: Optional[str] = None,
):

    # write feedback to file
    fname = datetime.now().isoformat()
    with open(fname, 'w') as file:
        print(f'action: {action}', file=file)
        print(f'pmid: {pmid}', file=file)
        print(f'table: {table}', file=file)
        print(f'token: {token}', file=file)

    # authenticate with azure
    az_key = 'AZURE_STORAGE_CONNECTION_STRING'
    if az_key not in os.environ:

        # load in azure authentication token
        conn_fname = join(os.environ['SECRETS_DIR'], 'litai-fileserver')
        if not isfile(conn_fname):
            return {
                'Status': 'Failed',
                'Reason': 'Could not authenticate with Azure. '
                          f'File {conn_fname} DNE',
            }

        # add to env vars
        os.environ[az_key] = open(conn_fname, 'r').read()

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
    return {'Status': 'Succeeded'}
