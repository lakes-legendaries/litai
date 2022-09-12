"""Simple commands to create the comments table"""

from litai.search import SearchEngine


# run only as cli
if __name__ == '__main__':

    # initialize engine
    engine = SearchEngine()._engine

    # create comments table
    engine.execute(
        """
            CREATE TABLE comments (
                _ROWID_ INT NOT NULL AUTO_INCREMENT,
                Date DATETIME,
                PMID INT NOT NULL,
                Token VARCHAR(64) NOT NULL,
                User VARCHAR(32) NOT NULL,
                ScoresTable VARCHAR(32),
                Comment VARCHAR(2048) NOT NULL,
                PRIMARY KEY(_ROWID_),
                KEY(PMID),
                KEY(Token),
                KEY(User),
                KEY(ScoresTable)
            )
        """
    )
