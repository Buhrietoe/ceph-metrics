FROM centos:centos7

ENV TELEGRAF_VERSION 0.13.0

WORKDIR /usr/local/bin

COPY ceph.repo /etc/yum.repos.d/ceph.repo

RUN yum install -y epel-release && \
    yum install -y python python-pip python-virtualenv ceph && \
    yum install -y https://dl.influxdata.com/telegraf/releases/telegraf-${TELEGRAF_VERSION}.x86_64.rpm && \
    yum clean all -y

COPY telegraf.conf /etc/telegraf/

CMD telegraf
