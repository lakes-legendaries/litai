FROM python:3.9-slim

# setup unix
RUN apt-get update
RUN apt-get install -y default-libmysqlclient-dev g++ git wget

# setup python
RUN pip install --upgrade pip

# setup app
ENV SECRETS_DIR /secrets
CMD [ \
    "uvicorn", "litai.app:app", "--host", "0.0.0.0", "--port", "443", \
    "--ssl-keyfile=/secrets/privkey.pem", \
    "--ssl-certfile=/secrets/fullchain.pem" \
]

# install litai
RUN pip install git+https://github.com/lakes-legendaries/litai.git
