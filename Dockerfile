FROM debian:buster-slim

ENV ANSIBLE_STDOUT_CALLBACK=default
ENV ANSIBLE_RETRY_FILES_ENABLED=0
ENV ANSIBLE_SSH_RETRIES=20
ENV ANSIBLE_SSH_ARGS="-o ServerAliveInterval=30 -o ControlMaster=auto -o ControlPersist=60s"

RUN apt update && apt install -y gnupg2 && \
    echo "deb http://ppa.launchpad.net/ansible/ansible-2.8/ubuntu trusty main" > /etc/apt/sources.list.d/ansible.list && \
    apt-key adv --keyserver keyserver.ubuntu.com --recv-keys 93C4A3FD7BB9C367

RUN apt update && apt install -y ansible git

RUN rm -rf /var/cache/apt/

RUN mkdir -p /root/.ssh

COPY ./kypo-ansible-runner.sh /app/

WORKDIR /app

# /app/inventory.ini
ENTRYPOINT ["./kypo-ansible-runner.sh", "-i", "inventory.ini"]
# docker inspect c2c769c4b9ef --format='{{.State.ExitCode}}'
