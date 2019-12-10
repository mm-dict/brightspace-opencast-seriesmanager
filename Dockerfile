FROM python:3.6-alpine
MAINTAINER Multimedia <multimedia@ugent.be>
ENV PS1="\[\e[0;33m\]|> seriesmanager <| \[\e[1;35m\]\W\[\e[0m\] \[\e[0m\]# "

WORKDIR /src
COPY . /src
COPY config/seriesmanager.yml /etc/seriesmanager/seriesmanager.yml

RUN pip install --no-cache-dir -r requirements.txt \
    && python setup.py install
WORKDIR /
ENTRYPOINT ["seriesmanager"]
