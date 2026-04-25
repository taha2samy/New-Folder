FROM paketobuildpacks/build-ubi8-base AS build
USER root
RUN microdnf install -y gcc gcc-c++ make libffi-devel openssl-devel zlib-devel
USER cnb

FROM paketobuildpacks/run-ubi8-base AS run
USER cnb