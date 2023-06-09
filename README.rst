###################################
LitAI: AI-Powered Literature Search
###################################

===================
Deprectation Notice
===================

This project has been discontinued, and the search engine / API links below will no longer work.
The code will continue to be hosted here as a code sample to jumpstart future projects.

===============
Original README
===============

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
<https://litaifileserver.z13.web.core.windows.net/>`_. This app is also hosted as an `API
on Azure <https://litai.eastus.cloudapp.azure.com>`_. For more details on the
algorithm, check out the `docs <https://lakes-legendaries.github.io/litai/>`_.
If you will be contributing to this repo, see the `developer guide
<https://lakes-legendaries.github.io/litai/dev.html>`_.
