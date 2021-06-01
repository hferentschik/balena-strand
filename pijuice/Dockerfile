FROM balenalib/raspberrypi3-64-python:3-buster

RUN echo 'deb http://archive.raspberrypi.org/debian/ buster main' >> /etc/apt/sources.list
RUN apt-key adv --recv-keys --keyserver keyserver.ubuntu.com 82B129927FA3303E
RUN apt-get update \
 && apt-get install -y curl jq pijuice-gui openssh-server tzdata \
 && apt-get clean \
 && rm -rf /var/lib/apt/lists/*

RUN mkdir /var/run/sshd \
 && echo 'root:balena' | chpasswd \
 && sed -i 's/#PermitRootLogin prohibit-password/PermitRootLogin yes/' /etc/ssh/sshd_config \
 && sed -i 's/UsePAM yes/UsePAM no/' /etc/ssh/sshd_config

WORKDIR /app

COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt

COPY main.py main.py
COPY pijuice_util.py pijuice_util.py
COPY start.sh start.sh

COPY balena.cfg /root/.balena/balena.cfg

ENV UDEV=1
ENV TZ=Europe/Stockholm

CMD ./start.sh
