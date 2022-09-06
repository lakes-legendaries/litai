FROM python:3.9-slim

# set workdir
WORKDIR /code

# setup unix
RUN apt-get update
RUN apt-get install -y default-libmysqlclient-dev

# setup python
RUN python -m pip install --upgrade pip
RUN python -m pip install fastapi numpy pandas sqlalchemy uvicorn

# setup app
ENV SECRETS_DIR /secrets
COPY litai/ litai/
CMD [ \
    "uvicorn", "litai.app:app", "--host", "0.0.0.0", "--port", "443", \
    "--ssl-keyfile=/secrets/privkey.pem", \
    "--ssl-certfile=/secrets/fullchain.pem" \
]
