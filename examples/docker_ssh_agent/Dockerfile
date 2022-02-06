FROM python:slim AS build-deps
RUN set -eux; \
    mkdir -p /etc/ssh; \
    echo 'github.com ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIOMqqnkVzrm0SdG6UOoqKLsabgH5C9okWi0dh2l9GKJl' >> /etc/ssh/ssh_known_hosts; \
    chmod 644 /etc/ssh/ssh_known_hosts
RUN set -eux; \
    apt-get update; \
    apt-get install --assume-yes --no-install-recommends \
        git="*" \
        openssh-client="*" \
    ; \
    rm -rf /var/lib/apt/lists/*
