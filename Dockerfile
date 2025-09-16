FROM python:3.12-slim-bookworm

ENV ANSIBLE_STDOUT_CALLBACK=default
ENV ANSIBLE_RETRY_FILES_ENABLED=0
ENV ANSIBLE_SSH_RETRIES=20
ENV ANSIBLE_SSH_ARGS="-o ServerAliveInterval=30 -o ControlMaster=auto -o ControlPersist=60s"

RUN apt update && apt install -y gnupg2 git autossh

RUN pip3 install ansible==9.* pypsrp requests[socks] crczp-automated-problem-generation-lib netaddr

RUN ansible-galaxy collection install community.docker:3.10.1

RUN rm -rf /var/cache/apt/

RUN mkdir -p /root/.ssh

COPY ./entrypoint.sh /app/
COPY manage_answers.py /app/

WORKDIR /app

# /app/inventory.ini
ENTRYPOINT ["./entrypoint.sh", "-i", "inventory.ini"]
# docker inspect c2c769c4b9ef --format='{{.State.ExitCode}}'
