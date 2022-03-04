FROM python:3.9-slim

# attach to repo
LABEL org.opencontainers.image.source https://github.com/lakes-legendaries/litai

# set workdir
WORKDIR /code

# setup unix
RUN apt-get update
RUN apt-get install -y g++
RUN apt-get clean

# setup python
COPY Dockerfile.requirements .
RUN python -m pip install --upgrade pip
RUN python -m pip install -r Dockerfile.requirements
RUN rm Dockerfile.requirements
ENV PYTHONPATH .

# copy databases
COPY data/hbot.db data/
COPY data/senescence.db data/

# setup app
COPY litai/app.py litai/
COPY litai/search.py litai/
CMD ["uvicorn", "litai.app:app", "--host", "0.0.0.0", "--port", "80"]
