FROM python:3.5

WORKDIR /usr/local/chisubmit

COPY . .

RUN apt-get update && apt-get install -y libldap2-dev libsasl2-dev

RUN pip install -e .

RUN pip install -e .[server]

CMD [ "chisubmit", "--version" ]