##############
Infrastructure
##############

This app is hosted as an API and as a website. Here, we discuss the steps
necessary to make this project live.

*******
Website
*******

This app's search engine is hosted as a static website on Azure, with `this
primary endpoint <https://litaifileserver.z13.web.core.windows.net/>`_.

We use blob storage and the azure cli to automatically update the website when
the code and data files are updated (daily). See :code:`webserver/update.sh`
for the implementation.

If a valid token is provided as a URL parameter, then feedback links are
automatically included with each article. E.g. if you use the URL

.. code-block:: text

   https://litaifileserver.z13.web.core.windows.net/?token=VALID_TOKEN

then you will get options for accepting or rejecting articles.

.. note::

   When we retrain the model, we only accept feedback from users who provide a
   validated token. Contact us at :code:`mike@lakeslegendaries.com` if you'd
   like to provide feedback.

***
API
***

This app's API is hosted on an Ubuntu 20.04 Azure VM. The VM can be properly
provisioned by placing the Azure blob storage connection string corresponding
to the website's account in :code:`~/secrets/litai-fileserver`, and then
running:

.. code-block:: bash

   curl https://raw.githubusercontent.com/lakes-legendaries/litai/main/webserver/provision.sh | bash

This command:

#. Installs the docker engine
#. Installs the Azure CLI
#. Uses certbot to create a secure https connection
#. Schedules monthly reboots
#. Schedules daily data/website updates
#. Triggers a startup script :code:`webserver/startup.sh` to start the api on
   system startup
#. Clones this repo, and builds and launches this api docker service.

Please note that this command expects:

#. The DNS of the webserver to be set to
   :code:`litai.eastus.cloudapp.azure.com`
#. Ports 80 and 443 to be open
#. The main user to be named :code:`mike`
