#!/bin/bash

# error on failure
set -e

# setup unix
sudo apt-get update
sudo apt-get install -y ca-certificates curl git gnupg lsb-release

# access docker repository
KEYFILE=/usr/share/keyrings/docker-archive-keyring.gpg
sudo rm -f $KEYFILE
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o $KEYFILE
echo "deb [arch=$(dpkg --print-architecture) signed-by=$KEYFILE] \
    https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" \
    | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# install docker engine
sudo apt-get update
sudo apt-get install -y docker-ce docker-ce-cli containerd.io

# install azure cli
curl -sL https://aka.ms/InstallAzureCLIDeb | sudo bash

# get ssl/tls certificates for secure https connection
sudo apt-get install -y snapd
sudo snap install core
sudo snap refresh core
sudo apt-get remove -y certbot
sudo snap install --classic certbot
sudo ln --force -s /snap/bin/certbot /usr/bin/certbot
sudo /usr/bin/certbot certonly \
    --standalone -n --domains litai.eastus.cloudapp.azure.com \
    --agree-tos --email mike@lakeslegendaries.com

# clone repo
rm -rfd litai
git clone https://github.com/lakes-legendaries/litai.git

# download database
export AZURE_STORAGE_CONNECTION_STRING="$(cat /home/mike/secrets/litai-fileserver)"
az storage blob download -f litai/data/pubmed.db -c data -n pubmed.db

# schedule startup command, and plan monthly reboot
sudo rm /var/spool/cron/crontabs/$USER
sudo rm /var/spool/cron/crontabs/root
echo "@reboot /home/mike/litai/webserver/startup.sh" | sudo tee /var/spool/cron/crontabs/$USER
echo "0 1 * * * /home/mike/litai/webserver/update.sh" | sudo tee -a /var/spool/cron/crontabs/$USER
echo "0 0 1 * * reboot" | sudo tee /var/spool/cron/crontabs/root
sudo chmod 0600 /var/spool/cron/crontabs/$USER
sudo chmod 0600 /var/spool/cron/crontabs/root

# run startup script
/home/mike/litai/webserver/startup.sh
