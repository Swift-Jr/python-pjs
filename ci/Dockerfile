# Image to be used on CI only
# docker build . -t python-psql:3.7 --no-cache
# docker tag python-psql:3.7 platfi.azurecr.io/utils/python-psql:3.7
# docker push platfi.azurecr.io/utils/python-psql:3.7
FROM python:3.7

RUN apt update && \
    apt install -y postgresql-client
