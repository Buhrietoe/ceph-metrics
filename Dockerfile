FROM centos:centos7

WORKDIR /usr/local/bin

COPY ceph.repo /etc/yum.repos.d/ceph.repo

RUN yum install -y epel-release && \
    yum install -y python python-pip python-virtualenv ceph && \
    yum install -y https://dl.influxdata.com/telegraf/releases/telegraf-0.13.0.x86_64.rpm && \
    yum clean all -y

CMD telegraf
