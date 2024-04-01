#!/bin/bash

if [ -x "$(command -v plum)" ]; then
    echo "Generating portable Plum release..."
else
    echo "Plum is not installed, attempting to install it first..."
    curl https://raw.githubusercontent.com/LouisDupraz/Plum/main/plum_install.sh | bash
    if [ "$?" != "0" ]; then
        echo "Plum installation failed, exiting..."
        exit 1
    fi
fi

sudo rm -rf /tmp/Plum
git clone https://github.com/LouisDupraz/Plum.git /tmp/Plum

mkdir -p release
cd release

cp /tmp/Plum/__main__.py .
cp /tmp/Plum/plum_update.sh .
cp /tmp/Plum/VERSION .
cp /tmp/Plum/code-style-checker .
cp /tmp/Plum/code_style_c.py .
cp /tmp/Plum/code_style_haskell.py .
cp /tmp/Plum/install_release.sh .

sudo cp /bin/lambdananas .

curr_user="$(whoami)"
sudo cp -r /usr/local/lib/vera++ ./vera++-lib
sudo chown -R "$curr_user" vera++-lib

curr_dir="$(pwd)"
function build_vera() {
    sudo rm -rf /tmp/banana-vera
    git clone https://github.com/Epitech/banana-vera.git /tmp/banana-vera
    cd /tmp/banana-vera

    boost_version=$(cat src/boost.cmake | grep "set(Boost_VERSION " | cut -d' ' -f4 | sed 's/)//g')
    boost_mirror=$(cat src/boost.cmake | grep "set(BOOST_MIRROR" | cut -d' ' -f4)
    new_boost_mirror=$(echo $boost_mirror | sed "s|$boost_mirror|netcologne.dl.sourceforge.net|g")
    boost_url=$(cat src/boost.cmake | grep "set(Boost_URL " | cut -d'"' -f2)
    boost_file="boost_$(echo "$boost_version" | tr '.' '_').tar.bz2"
    new_boost_url=$(echo 'https://${BOOST_MIRROR}/project/boost/boost/'"$boost_version/$boost_file")
    sed -i "s|$boost_mirror|$new_boost_mirror|g" src/boost.cmake
    sed -i "s|$boost_url|$new_boost_url|g" src/boost.cmake
    sed -i 's|add_executable(vera ${srcs})|add_executable(vera ${srcs})\ntarget_compile_options(vera PRIVATE\n  -O3\n  -march=native\n)|g' src/CMakeLists.txt

    cmake -B build . -DVERA_LUA=OFF -DPANDOC=OFF > /dev/null
    cmake --build build -j12 > /dev/null
    sudo cp build/src/vera++ /tmp/banana-vera/vera++
}
build_vera
cd "$curr_dir"

cp /tmp/banana-vera/vera++ .
tar -czvf "plum.tar.gz" plum plum_update.sh VERSION code-style-checker code_style_c.py code_style_haskell.py vera++ lambdananas vera++-lib install_release.sh

cp "plum.tar.gz" ..
cd ..
rm -rf release
