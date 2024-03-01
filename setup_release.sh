#!/bin/bash

if [ -x "$(command -v plum)" ]; then
    echo "Generating portable Plum release..."
else
    echo "Plum is not installed, please run install Plum first"
    exit 1
fi

rm -rf /tmp/Plum
git clone https://github.com/LouisDupraz/Plum.git /tmp/Plum

mkdir -p release
cd release

cp /tmp/Plum/plum .
cp /tmp/Plum/plum_update.sh .
cp /tmp/Plum/VERSION .
cp /tmp/Plum/code-style-checker .
cp /tmp/Plum/code_style_c.py .
cp /tmp/Plum/code_style_haskell.py .
cp /tmp/Plum/install_release.sh .

sudo cp /usr/local/bin/vera++ .
sudo cp /bin/lambdananas .

curr_user="$(whoami)"
sudo cp -r /usr/local/lib/vera++ ./vera++-lib
sudo chown -R "$curr_user" vera++-lib

VERSION="$(cat VERSION)"

tar -czvf "plum-$VERSION.tar.gz" plum plum_update.sh VERSION code-style-checker code_style_c.py code_style_haskell.py vera++ lambdananas vera++-lib install_release.sh

cp "plum-$VERSION.tar.gz" ..
cd ..
rm -rf release
