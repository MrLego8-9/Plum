#!/bin/bash

CURRDIR=$(pwd)

if [ -f /usr/lib/libluabind.so ]; then
echo ""
else
echo -e "Installing luabind\n\n"

cd /tmp
rm -rf luabind/
git clone https://github.com/ryzom/luabind.git
mkdir luabind/build
cd luabind/build
cmake -DLUABIND_DYNAMIC_LINK=ON -DCMAKE_INSTALL_PREFIX=/usr ..
make DESTDIR="/" install
cd /usr/lib
sudo ln -s libluabind09.so libluabind.so
echo ""
fi

echo -e "\nInstalling Plum\n\n"

sudo cp lambdananas /bin
sudo cp plum /bin

sudo mkdir -p /opt/plum-coding-style
sudo cp code-style* /opt/plum-coding-style

sudo cp bin/vera++ /usr/local/bin/
sudo cp -r lib/vera++ /usr/local/lib


