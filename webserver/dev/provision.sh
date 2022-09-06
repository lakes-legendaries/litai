#!/bin/bash

# error on failure
set -e

# setup unix
sudo apt-get update
sudo apt-get upgrade -y
sudo apt-get dist-upgrade -y
sudo apt-get install -y \
    build-essential \
    ca-certificates \
    curl \
    default-libmysqlclient-dev \
    g++ \
    gnupg \
    lsb-release \
    software-properties-common \

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

# upgrade python
sudo add-apt-repository -y ppa:deadsnakes/ppa
sudo apt-get install -y python3.9 python3.9-dev python3.9-venv

# set up basic aliases and environmental variables
echo "alias python=python3.9" > ~/.bash_aliases
echo "alias venv=\"source .venv/bin/activate\"" >> ~/.bash_aliases
echo "export PYTHONPATH=\".:/home/mike/litai\"" >> ~/.bash_aliases
echo "export SECRETS_DIR=\"/home/mike/secrets\"" >> ~/.bash_aliases

# clone repo
rm -rfd ~/litai
git clone https://github.com/lakes-legendaries/litai.git

# setup python environment
python3.9 -m venv ~/litai/.venv
source ~/litai/.venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r ~/litai/requirements.txt

# download training data
export AZURE_STORAGE_CONNECTION_STRING="$(cat /home/mike/secrets/litai-fileserver)"
az storage blob download -f /home/mike/litai/data/senescence_pmids.txt -c data -n senescence_pmids.txt

# schedule daily updates
sudo rm -f /var/spool/cron/crontabs/$USER
sudo rm -f /var/spool/cron/crontabs/root
echo "0 4 * * * /home/mike/litai/webserver/dev/update.sh" | sudo tee /var/spool/cron/crontabs/$USER
echo "0 0 1 * * reboot" | sudo tee /var/spool/cron/crontabs/root
sudo chmod 0600 /var/spool/cron/crontabs/$USER
sudo chmod 0600 /var/spool/cron/crontabs/root
