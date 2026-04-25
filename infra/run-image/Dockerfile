FROM ubuntu:24.04

RUN apt-get update && apt upgrade -y && apt-get install -y ca-certificates && rm -rf /var/lib/apt/lists/* && \
    groupadd -g 1001 cnb && \
    useradd -u 1001 -g cnb -s /bin/bash -m cnb

LABEL io.buildpacks.stack.id="io.buildpacks.stacks.noble"

USER cnb
