##########
Quickstart
##########

All of the programs in this package have an easy command-line interface for
executing this algorithm's major functions. Here, we provide a guide for
quickly running this pipeline.

Please note that this page is a developer's guide for running this package's
programs locally, and NOT for accessing the API on our webserver.

***********************
Set up your environment
***********************

.. note::

    For all code samples in this documentation, we've aliased
    :code:`python=python3.9`.

This package requires the unix utilities :code:`wget` and :code:`g++`. Once
you've installed those, install the required python packages. We recommend
using a virtual environment, e.g.

.. code-block:: bash

   python -m venv .venv
   source .venv/bin/activate
   python -m pip install --upgrade pip
   python -m pip install -r requirements.txt

*****************
Create a Database
*****************

You'll need to create a local mirror of PubMed as a SQLite database. This code
is default-configured to grab every article published since 2010, and will take
several hours to run.

This operation is run in two parts: As a :code:`get-files` command, which
downloads the file list from PubMed servers; and as a python command that
creates the actual database by invoking the :class:`~litai.db.DataBase` class.

To create your database, run:

.. code-block:: bash

   cmd/get-files
   python litai/db.py --create

Results will be saved as :code:`data/pubmed.db`

*************************
Provide Training Articles
*************************

To train this algorithm, you must provide it with examples of the kinds of
articles you want it to find. You can do this by specifying four different
quantities:

#. :code:`pos_pmids`: Representative of articles you want. Ideally, there
   should be 10s-100s of these. You should always provide this and/or
   :code:`pos_keywords`
#. :code:`neg_pmids`: Representative of articles you DON'T want. This is
   optional, but improves results.
#. :code:`pos_keywords`: Include as a :code:`pos_pmid` all articles that match
   any of these keywords. It's OK to include only a few, or many, keywords.
#. :code:`neg_keywords`: Include as a :code:`neg_pmid` all articles that match
   any of these keywords. This is optional, but improves results.

Provide this list as a :code:`my_articles.yaml` file. Here's a sample:

.. code-block:: yaml

   pos_pmids:
     - 10337457
     - 11891847
     - 12028221
     - ...
   neg_pmids:
     - 24584157
     - 24643567
     - 75384168
     - ...
   pos_keywords:
     - hbot
     - hyperbaric oxygen
   neg_keywords:
     - mouse
     - fish

**************
Score Articles
**************

Your next step is to score articles by their relevance to the provided
articles. The actual scoring is done by the sklearn-compliant
:class:`~litai.model.TokenRegressor` class, which is wrapped by the
:class:`~litai.score.ArticleScorer` class.

Find relevant articles by running:

.. code-block:: bash

   python litai/score.py -c my_articles.yaml

where :code:`my_articles.yaml` is your yaml file created in the previous step.
This will output results to :code:`data/my_articles.db`.

*************
Query Results
*************

Results can then be queried from this database, e.g. with the
:class:`~litai.search.SearchEngine` class, e.g.:

.. code-block:: python

   from pandas import DataFrame
   
   from litai import SearchEngine


   # initialize engine
   engine = SearchEngine('data/my_articles.db')

   # get top-scoring 100 articles
   df: DataFrame = engine.search(
       limit=100,
    )

   # find articles matching all keywords
   df: DataFrame = engine.search(
       keywords=[
           'animal',
           'research',
       ],
       limit=100,
    )

   # find articles since date
   df: DataFrame = engine.search(
       keywords=[
           'animal',
           'research',
       ],
       min_date='2020-01-01',
       limit=100,
    )
