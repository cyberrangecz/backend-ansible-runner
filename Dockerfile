FROM python:3.8-slim-buster

ENV ANSIBLE_STDOUT_CALLBACK=default
ENV ANSIBLE_RETRY_FILES_ENABLED=0
ENV ANSIBLE_SSH_RETRIES=20
ENV ANSIBLE_SSH_ARGS="-o ServerAliveInterval=30 -o ControlMaster=auto -o ControlPersist=60s"

RUN apt update && apt install -y gnupg2 git autossh

RUN pip3 install ansible==3.0.0 pypsrp requests[socks]

RUN rm -rf /var/cache/apt/

RUN mkdir -p /root/.ssh

COPY ./kypo-ansible-runner.sh /app/

WORKDIR /app

# /app/inventory.ini
ENTRYPOINT ["./kypo-ansible-runner.sh", "-i", "inventory.ini"]
# docker inspect c2c769c4b9ef --format='{{.State.ExitCode}}'
