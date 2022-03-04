##############
Infrastructure
##############

The infrastructure for this project includes:

#. An Azure storage account, with the following containers:

   #. app (for hosting the browser-based search engine website)
   #. data (for hosting databases between runs)
   #. logs (for persisting logs after runs on batch)

#. An Azure container app
#. An Azure batch account
#. An image on the GitHub Container Registry (GHCR)

*****************
Automatic Updates
*****************

This project is hosted as an application accessible from a `browser-based
search engine <https://litai.blob.core.windows.net/app/search.html>`_.

This app is updated every week via the
:code:`.github/workflows/update-databases.yaml` Github Action. Because the
PubMed database is so large, and the update workflow is so intensive, we run
this update off-site on the Azure batch servers.

The json that controls the batch job is created with the :code:`cmd/batch-json`
script. Then, on the batch servers, the script :code:`cmd/update-databases` is
run, which:

#. Updates the PubMed database mirror with the most recent files
#. Re-generates the :code:`hbot` and :code:`senescence` database files with the
   :code:`litai/score.py` script
#. Updates the docker image hosted on the GHCR with the :code:`cmd/docker`
   command
#. Deletes old images in the GHCR with the :code:`cmd/delete_old.py` script
#. Reloads the container app on the Azure servers with the
   :code:`cmd/restart-con-app` command.
#. Persists data files in Azure storage
#. Updates the website with code from the :code:`html/` directory.

*******
Secrets
*******

The following secrets are stored:

#. On GitHub:

   #. To submit batch jobs:

      #. :code:`$AZURE_BATCH_ACCESS_KEY`
      #. :code:`$AZURE_BATCH_ACCOUNT`
      #. :code:`$AZURE_BATCH_ENDPOINT`

#. On Azure:

   #. To persist data files: :code:`$EZAZURE_TOKEN`
   #. To push to GHCR: :code:`$GIT_TOKEN`
   #. To reset the container app after updates:

      #. :code:`$SERVICE_PRINCIPAL_USER`
      #. :code:`$SERVICE_PRINCIPAL_PASSWORD`
      #. :code:`$SERVICE_PRINCIPAL_TENANT`
