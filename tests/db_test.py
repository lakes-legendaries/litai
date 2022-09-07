from pytest import fixture

from litai import DataBase, SearchEngine


@fixture(scope='session')
def test_db():

    # make db from scratch
    DataBase(
        'pytest',
        file_list=[
            'https://ftp.ncbi.nlm.nih.gov/pubmed/updatefiles/'
            'pubmed22n1120.xml.gz'
        ],
    ).create()

    # append to db
    count0 = SearchEngine('pytest').get_count()
    db = DataBase(
        'pytest',
        file_list=[
            'https://ftp.ncbi.nlm.nih.gov/pubmed/updatefiles/'
            'pubmed22n1121.xml.gz'
        ],
    )
    db.append()
    count1 = SearchEngine('pytest').get_count()
    assert (count1 > count0)

    # check shrinking
    assert (db._preshrink_count > db._postshrink_count)

    # try to re-append same
    count0 = SearchEngine('pytest').get_count()
    DataBase(
        'pytest',
        file_list=[
            'https://ftp.ncbi.nlm.nih.gov/pubmed/updatefiles/'
            'pubmed22n1121.xml.gz'
        ],
    ).append()
    count1 = SearchEngine('pytest').get_count()
    assert (count1 == count0)
