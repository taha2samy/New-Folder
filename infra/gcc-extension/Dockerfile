FROM paketobuildpacks/build-ubi9-base AS build
USER root
RUN microdnf install -y gcc gcc-c++ make libffi-devel openssl-devel zlib-devel
USER cnb

FROM paketobuildpacks/run-ubi9-base AS run
USER cnb