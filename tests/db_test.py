from os import remove

from pytest import fixture

from litai import DataBase, SearchEngine


# create example database
@fixture(scope="session", autouse=True)
def make_db(request):
    DataBase(
        database='data/example.db',
        file_list=[
            'https://ftp.ncbi.nlm.nih.gov/pubmed/updatefiles/'
            'pubmed22n1120.xml.gz'
        ],
    ).create()
    request.addfinalizer(lambda: remove('data/example.db'))


def test_append():
    count0 = SearchEngine(database='data/example.db').get_count()
    DataBase(
        database='data/example.db',
        file_list=[
            'https://ftp.ncbi.nlm.nih.gov/pubmed/updatefiles/'
            'pubmed22n1121.xml.gz'
        ],
    ).append()
    count1 = SearchEngine(database='data/example.db').get_count()
    assert (count1 > count0)
