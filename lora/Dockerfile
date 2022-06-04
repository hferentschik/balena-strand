FROM balenalib/raspberrypi3-64-python:3-buster

RUN apt-get update \
 && apt-get install -y build-essential \
                       curl \
                       gcc \
                       gettext \
                       git \
                       libffi-dev \
                       libgdbm-dev \
                       libncurses5-dev \
                       libnss3-dev \
                       libreadline-dev \
                       libssl-dev \
                       openssh-server \
                       sshfs \
                       software-properties-common \
                       vim \
                       wget\
                       zlib1g-dev
#  && apt-get clean \
#  && rm -rf /var/lib/apt/lists/*

RUN mkdir /var/run/sshd \
 && echo 'root:balena' | chpasswd \
 && sed -i 's/#PermitRootLogin prohibit-password/PermitRootLogin yes/' /etc/ssh/sshd_config \
 && sed -i 's/UsePAM yes/UsePAM no/' /etc/ssh/sshd_config

# Install Python 3.9.0 due to depdendency PyAudio failing with SystemError: PY_SSIZE_T_CLEAN on Python 3.10.x
# See https://stackoverflow.com/questions/70344884/pyaudio-write-systemerror-py-ssize-t-clean-macro-must-be-defined-for-format
RUN wget https://www.python.org/ftp/python/3.9.0/Python-3.9.0.tar.xz \
 && tar -xf Python-3.9.0.tar.xz \
 && cd Python-3.9.0 \
 && ./configure \
 && make install

WORKDIR /app

RUN git clone https://github.com/rm-hull/spidev-test \
 && cd spidev-test \
 && gcc spidev_test.c -o spidev_test \
 && cd ..

COPY requirements.txt requirements.txt
RUN pip3 install -r requirements.txt

COPY dragino/ dragino/
COPY dragino.template.toml .
COPY test.py .
COPY test_downlink.py .
COPY start.sh .
COPY main.py .

CMD ./start.sh
