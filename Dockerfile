FROM python:3.9-slim

# set workdir
WORKDIR /code

# setup unix
RUN apt-get update
RUN apt-get install -y g++ default-libmysqlclient-dev

# copy files
COPY . .

# setup python
RUN pip install --upgrade pip
RUN pip install .

# setup app
ENV SECRETS_DIR /secrets
CMD [ \
    "uvicorn", "litai.app:app", "--host", "0.0.0.0", "--port", "443", \
    "--ssl-keyfile=/secrets/privkey.pem", \
    "--ssl-certfile=/secrets/fullchain.pem" \
]
