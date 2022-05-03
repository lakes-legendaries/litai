#!/bin/bash

# error on failure
set -e

# hush login
touch .hushlogin

# setup unix
sudo apt-get update -y
sudo apt-get upgrade -y
sudo apt-get dist-upgrade -y
sudo apt-get install -y \
    ca-certificates \
    curl \
    g++ \
    git \
    gnupg \
    lsb-release \
    snapd \
    software-properties-common \

# install python3.9
sudo add-apt-repository -y ppa:deadsnakes/ppa
sudo apt install -y python3.9 python3.9-dev python3.9-venv

# install azure cli
curl -sL https://aka.ms/InstallAzureCLIDeb | sudo bash

# get ssl/tls certificates for secure https connection
sudo snap install core
sudo snap refresh core
sudo apt-get remove -y certbot
sudo snap install --classic certbot
sudo ln --force -s /snap/bin/certbot /usr/bin/certbot
sudo certbot certonly \
    --standalone -n --domains litai.eastus.cloudapp.azure.com \
    --agree-tos --email mike@lakeslegendaries.com

# edit crontab
CRONTAB_DIR=/var/spool/cron/crontabs
SCRIPTS_DIR=/home/$USER/litai/webserver
sudo rm -f $CRONTAB_DIR/*
echo "@reboot $SCRIPTS_DIR/reboot.sh" | sudo tee $CRONTAB_DIR/$USER
echo "0 4 * * * $SCRIPTS_DIR/update.sh" | sudo tee --append $CRONTAB_DIR/$USER
echo "0 3 1 * * reboot" | sudo tee $CRONTAB_DIR/root
for CRONTAB in root $USER; do
    sudo chmod 0600 $CRONTAB_DIR/$CRONTAB
done

# clone repo, download database
export AZURE_STORAGE_CONNECTION_STRING="$(cat /home/$USER/secrets/litai-fileserver)"
git clone https://github.com/lakes-legendaries/litai.git
az storage blob download -f litai/data/pubmed.db -c data -n pubmed.db

# create virtual environment
cd /home/$USER/litai
rm -rfd .venv
python3.9 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt

# run startup script
$SCRIPTS_DIR/reboot.sh
