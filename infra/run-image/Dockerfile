FROM registry.access.redhat.com/ubi8/ubi-minimal:latest

RUN microdnf install -y shadow-utils ca-certificates && \
    microdnf clean all

RUN groupadd -g 1000 cnb && \
    useradd -u 1000 -g cnb -s /bin/bash -m cnb

LABEL io.buildpacks.stack.id="io.buildpacks.stacks.ubi8"

USER cnb