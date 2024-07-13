#!/bin/bash

function install_deps() {
if [ -x "$(command -v dnf)" ]; then
    sudo dnf install --refresh -y tcl-devel python3-devel python3-pylint python3-clang || (echo "=> Error: dependency install went wrong"; exit 1)
elif [ -x "$(command -v apt-get)" ]; then
    sudo apt-get update
    DEBIAN_FRONTEND=noninteractive TZ=Etc/UTC sudo apt-get -y install tcl-dev python3-dev libpython3-dev pylint python3-clang || (echo "=> Error: dependency install went wrong" exit 1)
else
    echo "=> Error: Your distribution is not supported, please install the following packages manually:"
    echo "   - tcl / tcl-dev"
    echo "   - python3 / python3-dev"
    echo "   - pylint"
    echo "   - python3-clang"
fi
}

echo "Installing Plum release..."
sudo cp vera++ /usr/local/bin/
sudo cp lambdananas /bin
sudo cp -r vera++-lib /usr/local/lib
sudo mv /usr/local/lib/vera++-lib /usr/local/lib/vera++
sudo rm -f /bin/plum
sudo cp plum /bin

install_deps

echo "Plum release installed"
