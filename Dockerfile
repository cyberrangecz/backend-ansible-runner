FROM alpine:3.10

ENV ANSIBLE_STDOUT_CALLBACK=default
ENV ANSIBLE_RETRY_FILES_ENABLED=0
ENV ANSIBLE_SSH_RETRIES=20

RUN apk --update add --no-cache ansible bash git openssh

COPY ./kypo-ansible-runner.sh /app/

WORKDIR /app

# /app/inventory.ini
ENTRYPOINT ["./kypo-ansible-runner.sh", "-i", "inventory.ini"]
# docker inspect c2c769c4b9ef --format='{{.State.ExitCode}}'
