FROM ubuntu:22.04 AS builder

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get upgrade -y && apt-get install -y \
    ca-certificates \
    libssl3 \
    libstdc++6 \
    tzdata \
    curl \
    bash \
    && rm -rf /var/lib/apt/lists/*
FROM scratch
COPY --from=builder / /
RUN groupadd -g 1001 cnb && \
    useradd -u 1001 -g cnb -s /bin/bash -m cnb

LABEL io.buildpacks.stack.id="io.buildpacks.stacks.jammy"

USER cnb