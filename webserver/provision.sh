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

# setup self-hosted runner
rm -rfd actions-runner
mkdir actions-runner
cd actions-runner
curl -o actions-runner-linux-x64-2.296.1.tar.gz -L https://github.com/actions/runner/releases/download/v2.296.1/actions-runner-linux-x64-2.296.1.tar.gz
tar xzf ./actions-runner-linux-x64-2.296.1.tar.gz
./config.sh remove --token AOQ3VBZPEQUMZF3YAWWOA6DDD5D3O
./config.sh --unattended --url https://github.com/lakes-legendaries/litai --token AOQ3VBZPEQUMZF3YAWWOA6DDD5D3O
cd ..

# schedule restart and daily updates
CRONDIR="/var/spool/cron/crontabs"
ACTIONSDIR="/home/mike/litai/webserver"
sudo rm -f $CRONDIR/$USER
sudo rm -f $CRONDIR/root
echo "0 4 * * * $ACTIONSDIR/update.sh" | sudo tee $CRONDIR/$USER
echo "@reboot $ACTIONSDIR/run-service.sh" | sudo tee -a $CRONDIR/$USER
echo "@reboot /home/mike/actions-runner/run.sh" | sudo tee -a $CRONDIR/$USER
echo "0 0 1 * * reboot" | sudo tee $CRONDIR/root
sudo chmod 0600 $CRONDIR/$USER
sudo chmod 0600 $CRONDIR/root

# reboot
sudo reboot
