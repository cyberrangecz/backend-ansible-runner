FROM python:3.8-slim-buster

ENV ANSIBLE_STDOUT_CALLBACK=default
ENV ANSIBLE_RETRY_FILES_ENABLED=0
ENV ANSIBLE_SSH_RETRIES=20
ENV ANSIBLE_SSH_ARGS="-o ServerAliveInterval=30 -o ControlMaster=auto -o ControlPersist=60s"
ENV PIP_EXTRA_INDEX_URL="https://gitlab.ics.muni.cz/api/v4/projects/2358/packages/pypi/simple"

RUN apt update && apt install -y gnupg2 git autossh

RUN pip3 install ansible==3.0.0 pypsrp requests[socks] automated-problem-generation-lib

RUN rm -rf /var/cache/apt/

RUN mkdir -p /root/.ssh

COPY ./entrypoint.sh /app/
COPY prepare_answers.py /app/

WORKDIR /app

# /app/inventory.ini
ENTRYPOINT ["./entrypoint.sh", "-i", "inventory.ini"]
# docker inspect c2c769c4b9ef --format='{{.State.ExitCode}}'
