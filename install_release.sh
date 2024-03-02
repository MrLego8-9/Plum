#!/bin/bash

function install_deps() {
if [ -x "$(command -v dnf)" ]; then
    sudo dnf install --refresh -y tcl-devel python3-devel python3-pylint python3-clang || (tput setaf 1; echo "=> Error: dependency install went wrong"; tput sgr0; exit 1)
elif [ -x "$(command -v apt-get)" ]; then
    sudo apt-get update
    DEBIAN_FRONTEND=noninteractive TZ=Etc/UTC sudo apt-get -y install tcl-dev python3-dev libpython3-dev pylint python3-clang || (tput setaf 1; echo "=> Error: dependency install went wrong"; tput sgr0; exit 1)
else
    tput setaf 1
    echo "=> Error: Your distribution is not supported, please install the following packages manually:"
    echo "   - tcl / tcl-dev"
    echo "   - python3 / python3-dev"
    echo "   - pylint"
    echo "   - python3-clang"
    tput sgr0
fi
}

echo "Installing Plum release..."

sudo cp plum /bin
sudo mkdir -p /opt/plum-coding-style
sudo cp code-style* /opt/plum-coding-style/
sudo cp code_style* /opt/plum-coding-style/
sudo cp VERSION /opt/plum-coding-style/
sudo cp plum_update.sh /opt/plum-coding-style/

sudo cp vera++ /usr/local/bin/
sudo cp lambdananas /bin
sudo cp -r vera++-lib /usr/local/lib
sudo mv /usr/local/lib/vera++-lib /usr/local/lib/vera++

install_deps

echo "Plum release installed"
