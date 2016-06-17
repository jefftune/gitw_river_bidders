FROM        docker-dev.ops.tune.com/itops/baseimages-centos7:latest
MAINTAINER  jefft@tune.com

RUN mkdir -p /usr/local/src/ && \
   curl https://bootstrap.pypa.io/get-pip.py -o /usr/local/src/get-pip.py && \
   python /usr/local/src/get-pip.py && \
   python -m pip install --upgrade pip && \
   mkdir -p /usr/local/src/client/

COPY . /usr/local/src/client/

WORKDIR /usr/local/src/client/

RUN python --version
RUN python -m pip install --upgrade -r requirements.txt

EXPOSE 80

CMD ["python", "-u", "client.py"]
