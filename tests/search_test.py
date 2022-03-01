from litai import SearchEngine


def test_getters():
    engine = SearchEngine(database='data/example.db')
    count = engine.get_count()
    articles = next(engine.get_all(chunksize=int(1E6)))
    random = engine.get_rand(100)
    assert(count == articles.shape[0])
    assert(random.shape[0] == 100)


def test_keyword_search():
    keyword = 'mouse'
    engine = SearchEngine(database='data/example.db')
    df = engine.search(
        keywords=keyword,
    )
    for _, row in df.iterrows():
        assert(
            keyword in row['Title'].lower()
            or keyword in row['Keywords'].lower()
            or keyword in row['Abstract'].lower()
        )


def test_keyword_and_join():
    keywords = ['mouse', 'lifespan']
    engine = SearchEngine(database='data/example.db')
    df = engine.search(
        keywords=keywords,
        join='AND',
    )
    for _, row in df.iterrows():
        assert(
            keywords[0] in row['Title'].lower()
            or keywords[0] in row['Keywords'].lower()
            or keywords[0] in row['Abstract'].lower()
        )
        assert(
            keywords[1] in row['Title'].lower()
            or keywords[1] in row['Keywords'].lower()
            or keywords[1] in row['Abstract'].lower()
        )


def test_keyword_or_join():
    keywords = ['mouse', 'lifespan']
    engine = SearchEngine(database='data/example.db')
    df = engine.search(
        keywords=keywords,
        join='OR',
    )
    all_both = True
    for _, row in df.iterrows():
        assert(
            keywords[0] in row['Title'].lower()
            or keywords[0] in row['Keywords'].lower()
            or keywords[0] in row['Abstract'].lower()
            or keywords[1] in row['Title'].lower()
            or keywords[1] in row['Keywords'].lower()
            or keywords[1] in row['Abstract'].lower()
        )
        if not (
            keywords[0] in row['Title'].lower()
            or keywords[0] in row['Keywords'].lower()
            or keywords[0] in row['Abstract'].lower()
        ) or not (
            keywords[1] in row['Title'].lower()
            or keywords[1] in row['Keywords'].lower()
            or keywords[1] in row['Abstract'].lower()
        ):
            all_both = False
    assert(not all_both)


def test_pmid_search():
    pmids = [33999167, '33337786']
    engine = SearchEngine(database='data/example.db')
    df = engine.search(
        pmids=pmids,
    )
    assert(df.shape[0] == 2)
    assert(len(
        set([str(pmid) for pmid in pmids])
        .intersection(set(df['PMID'].to_numpy()))
    ) == 2)


def test_date_search():
    min_date = '2020-07-01'
    max_date = '2020-12-31'
    engine = SearchEngine(database='data/example.db')
    assert((engine.search(min_date=min_date)['Date'] >= min_date).all())
    assert((engine.search(max_date=max_date)['Date'] <= max_date).all())
    assert(all([
        min_date <= date <= max_date
        for date in engine.search(
            max_date=max_date,
            min_date=min_date,
        )['Date']
    ]))
