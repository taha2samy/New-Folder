FROM mcr.microsoft.com/devcontainers/python:1-3.11-bookworm

# Install additional OS packages
RUN apt-get update && export DEBIAN_FRONTEND=noninteractive \
    && apt-get -y install --no-install-recommends \
        curl \
        wget \
        git \
        jq \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# Install Task (go-task)
RUN sh -c "$(curl --location https://taskfile.dev/install.sh)" -- -d -b /usr/local/bin

# Install pack CLI (Cloud Native Buildpacks)
RUN (curl -sSL "https://github.com/buildpacks/pack/releases/download/v0.32.1/pack-v0.32.1-linux.tgz" | tar -C /usr/local/bin/ --no-same-owner -xzv pack)

# Switch to standard vscode user
USER vscode

# Install Python global dev tools
RUN pipx install pipenv
RUN pipx install poetry
