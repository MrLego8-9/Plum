FROM ubuntu:noble

RUN apt-get update && DEBIAN_FRONTEND=noninteractive TZ=Etc/UTC apt-get -y install tcl-dev python3-dev libpython3-dev pylint python3-clang wget sudo

COPY plum.tar.gz /plum.tar.gz

RUN mkdir plum-dir && tar -xvf plum.tar.gz -C ./plum-dir && rm plum.tar.gz && cd plum-dir && ./install_release.sh && cd .. && rm -rf plum-dir
