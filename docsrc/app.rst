##############
Infrastructure
##############

This app is hosted as an API and as a website. Here, we discuss the steps
necessary to make this project live.

*******
Website
*******

This app's search engine is hosted as a static website on Azure, with `this
primary endpoint <https://litai.z13.web.core.windows.net/>`_. `This CDN
<https://litai.azureedge.net/>`_ is then used to accelerate delivery to clients.

We use blob storage and the azure cli to automatically update the website when
the code and data files are updated (daily). See :code:`webserver/update.sh`
for the implementation.

***
API
***

This app's API is hosted on an Ubuntu 20.04 Azure VM. The VM can be properly
provisioned by placing the Azure blob storage connection string corresponding
to the website's account in :code:`~/secrets/litai-fileserver`, and then
running:

.. code-block:: bash

   curl https://raw.githubusercontent.com/lakes-legendaries/litai/main/webserver/provision.sh | sudo bash

This command:

#. Installs python
#. Installs the Azure CLI
#. Uses certbot to create a secure https connection
#. Schedules monthly reboots
#. Schedules daily data/website updates
#. Triggers a reboot script :code:`webserver/reboot.sh` to start the api on
   system startup
