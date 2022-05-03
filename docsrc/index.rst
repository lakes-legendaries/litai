##########################################
LitAI: AI-Powered PubMed Literature Search
##########################################

For the Methuselah Foundation.

This app searches the scientific literature to find articles that are relevant
to the mission of the Methuselah Foundation. It works by:

#. Ingesting a list of PubMed IDs or keywords,
#. Pulling relevant articles from PubMed, 
#. Using vector quantization to create numeric representations of each article,
#. Using AI/ML to score all articles based on their relevance.

While this app is currently configured to find anti-senescence research,
nothing in it is specific to this field.

You can see the results of this algorithm on our `Search Engine
<https://litai.azureedge.net/>`_. This app is also hosted as an `API on Azure
<litai.eastus.cloudapp.azure.com>`_. This app's code is publicly available on
`GitHub <https://github.com/lakes-legendaries/litai>`_.

*****************
Table Of Contents
*****************
.. toctree::
    :maxdepth: 1

    quickstart
    api
    app
    dev
