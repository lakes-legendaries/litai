from hashlib import sha512
from datetime import datetime
from secrets import token_urlsafe
from typing import Optional

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pandas import read_sql_query

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


# sanitize inputs
def sanitize(text: str) -> str:
    """Simple input sanitization

    Parameters
    ----------
    text: str
        input text

    Returns
    -------
    str
        sanitized input text
    """
    return (
        text.replace('"', '`')
            .replace("'", '`')
            .replace(';', ',')
    ) if text is not None else None


# verify allowed access
def authorized_user(session: str) -> str:
    """Verify if session is valid for an authorized user

    Parameters
    ----------
    session: str
        session token

    Returns
    -------
    str
        authorized username, or None of not an authorized session
    """
    user = SearchEngine()._engine.execute(f"""
        SELECT User from users
        WHERE Session = '{session}'
    """).fetchone()
    if len(user):
        return user[0]
    else:
        return None


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
    # connect to db
    se = SearchEngine()

    # pull articles from table
    articles = se.search(
        keywords=sanitize(keywords).split() if keywords else None,
        max_date=sanitize(max_date),
        min_date=sanitize(min_date),
        scores_table=sanitize(scores_table),
    )

    # return, if empty
    if articles.shape[0] == 0:
        return {}

    # pull corresponding comments
    comments = read_sql_query(
        f"""
            SELECT * FROM comments
            WHERE PMID IN ({
                ", ".join([
                    f'{pmid}'
                    for pmid in articles['PMID']
                ])
            })
        """,
        con=se._engine,
    )

    # return as json
    return {
        n: {
            'PMID': article['PMID'],
            'DOI': article['DOI'],
            'Title': article['Title'],
            'Abstract': article['Abstract'],
            'Date': article['Date'],
            'Score': article['Score'],
            'Comments': [
                {
                    'ID': comment['_ROWID_'],
                    'Date': comment['Date'],
                    'User': comment['User'],
                    'Comment': comment['Comment'],
                }
                for _, comment in comments.iterrows()
                if comment['PMID'] == article['PMID']
            ]
        }
        for n, article in articles.iterrows()
    }


@app.get('/comment/')
def comment(
    pmid: int,
    comment: str,
    session: str,
    scores_table: Optional[str] = None,
):
    if not (user := authorized_user(session)):
        return {
            'success': False,
            'reason': 'Unauthorized Session',
        }
    SearchEngine()._engine.execute(f"""
        INSERT INTO comments (
            Date,
            PMID,
            User,
            {'ScoresTable,' if scores_table else ''}
            Comment
        ) VALUES (
            NOW(),
            {pmid},
            "{user}",
            {f'"{sanitize(scores_table)}",' if scores_table else ''}
            "{sanitize(comment)}"
        )
    """)

    # return success
    return {'success': True}


@app.get('/delete-comment/')
def delete_comment(
    id: int,
    session: str,
):
    if not (user := authorized_user(session)):
        return {
            'success': False,
            'Reason': 'Unauthorized Session',
        }
    SearchEngine()._engine.execute(f"""
        DELETE FROM comments
        WHERE user = '{user}'
            AND _ROWID_ = {id}
    """)

    # return success
    return {'success': True}


@app.get('/feedback/')
def feedback(
    pmid: int,
    scores_table: str,
    feedback: float,
    session: str,
):
    if not (user := authorized_user(session)):
        return {
            'success': False,
            'reason': 'Unauthorized Session',
        }
    SearchEngine()._engine.execute(f"""
        INSERT INTO feedback (
            Date,
            PMID,
            User,
            ScoresTable,
            Feedback
        ) VALUES (
            NOW(),
            {pmid},
            "{user}",
            "{sanitize(scores_table)}",
            "{feedback}"
        )
    """)

    # return success
    return {'success': True}


def check_password(
    user: str,
    password: str,
) -> dict:
    """Check whether user/password combo is valid

    Parameters
    ----------
    user: str
        username
    password: str
        password

    Returns
    -------
    dict
        status dictionary
    """

    # sanitize
    user = sanitize(user)

    # connect to db
    engine = SearchEngine()._engine

    # check that user exists
    if not engine.execute(f"""
        SELECT COUNT(*) FROM users
        WHERE User = '{user}'
    """).fetchone()[0]:
        return {
            'success': False,
            'reason': 'User DNE',
        }

    # get last login attempt
    last_attempt = engine.execute(f"""
        SELECT LastLogin FROM users
        WHERE User = '{user}'
    """).fetchone()[0]

    # log current time as last attempt (regardless of success)
    current_time = datetime.now()
    engine.execute(f"""
        UPDATE users
        SET LastLogin = '{current_time.strftime('%Y-%m-%d %H:%M:%S')}'
        WHERE User = '{user}'
    """)

    # limit login attempts (to resist brute-force attacks)
    if (
        last_attempt is not None
        and (current_time - last_attempt).seconds < 3
    ):
        return {
            'success': False,
            'reason': 'Too many attempts. Wait 3 seconds and try again',
        }

    # check if password matches
    stored_hash, salt = engine.execute(f"""
        SELECT Hash, Salt FROM users
        WHERE User = '{user}'
    """).fetchone()
    if stored_hash == sha512(str.encode(salt + password)).hexdigest():
        return {'success': True}
    else:
        return {
            'success': False,
            'reason': f'Invalid password for user {user}',
        }


@app.get('/get-session/')
def get_session(
    user: str,
    password: str,
):
    # check password
    user = sanitize(user)
    status = check_password(user, password)

    # return failure
    if not status['success']:
        return status

    # create session
    session = token_urlsafe(1024)
    SearchEngine()._engine.execute(f"""
        UPDATE users
        SET Session = '{session}'
        WHERE User = '{user}'
    """)

    # return session token
    status['session'] = session
    return status


@app.get('/change-password/')
def change_password(
    user: str,
    old_password: str,
    new_password: str,
):
    # check password
    user = sanitize(user)
    status = check_password(user, old_password)

    # return failure
    if not status['success']:
        return status

    # get salt
    salt = SearchEngine()._engine.execute(f"""
        SELECT Salt FROM users
        WHERE User = '{user}'
    """).fetchone()[0]

    # change password
    hashed = sha512(str.encode(salt + new_password)).hexdigest()
    SearchEngine()._engine.execute(f"""
        UPDATE users
        SET Hash = '{hashed}'
        WHERE User = '{user}'
    """)

    # return success
    return {'success': True}
