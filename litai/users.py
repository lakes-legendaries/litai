"""Interface for managing the users login table"""
from argparse import ArgumentParser
from hashlib import sha512
from secrets import token_urlsafe

from litai.search import SearchEngine


# cli
if __name__ == '__main__':

    # parse cli
    parser = ArgumentParser(
        description=(
            'Manage the users login table.'
            ' Only one operation can be performed each call.'
        ),
    )
    parser.add_argument(
        '--create_table',
        default=False,
        action='store_true',
        help='Create login table',
    )
    parser.add_argument(
        '--add_user',
        default=None,
        help='Add an authorized user USERNAME',
    )
    parser.add_argument(
        '--remove_user',
        default=None,
        help='Remove an authorized user USERNAME',
    )
    parser.add_argument(
        '--delete_table',
        default=False,
        action='store_true',
        help='Delete login table',
    )
    args = parser.parse_args()

    # create table from scratch
    if args.create_table:
        query = """
            CREATE TABLE users (
                _ROWID_ INT NOT NULL AUTO_INCREMENT,
                User VARCHAR(32) NOT NULL UNIQUE,
                Salt TEXT NOT NULL,
                Hash TEXT NOT NULL,
                LastLogin DATETIME,
                Session TEXT,
                PRIMARY KEY(_ROWID_),
                KEY(User),
                KEY(Session(256))
            )
        """
    elif args.add_user:
        password = token_urlsafe(512)
        salt = token_urlsafe(512)
        hashed_password = sha512(str.encode(salt + password)).hexdigest()
        query = f"""
            INSERT INTO users (User, Salt, Hash)
            VALUES ('{args.add_user}', '{salt}', '{hashed_password}')
        """
        print(f'Username: {args.add_user}')
        print(f'Password: {password}')
    elif args.remove_user:
        query = f"""
            DELETE FROM users
            WHERE User = '{args.remove_user}'
        """
    elif args.delete_table:
        response = input(
            'WARNING: Login table will be dropped. Continue? [y/n] '
        )
        if response == 'y':
            query = """
                DROP TABLE users
            """
        else:
            quit()

    # run query
    engine = SearchEngine()._engine
    engine.execute(query)
