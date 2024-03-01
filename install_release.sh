#!/bin/bash

echo "Installing Plum release..."

sudo cp plum /bin
sudo mkdir -p /opt/plum-coding-style
sudo cp code-style* /opt/plum-coding-style/
sudo cp VERSION /opt/plum-coding-style/
sudo cp plum_update.sh /opt/plum-coding-style/

sudo cp vera++ /usr/local/bin/
sudo cp lambdananas /bin
sudo cp -r vera++-lib /usr/local/lib
sudo mv /usr/local/lib/vera++-lib /usr/local/lib/vera++

echo "Plum release installed"
