#!/bin/bash
sudo rm -rf /tmp/Plum
git clone https://github.com/LouisDupraz/Plum.git /tmp/Plum

function install_deps() {
if [ -x "$(command -v dnf)" ]; then
    sudo dnf install tcl-devel boost-devel git cmake make gcc-c++ python3-devel which pip python3-pylint || (tput setaf 1; echo "=> Error: dependency install went wrong"; tput sgr0; exit 1)
elif [ -x "$(command -v apt-get)" ]; then
    sudo apt-get install tcl-dev libboost-dev git cmake make build-essential python3-dev libpython3-dev which pip pylint || (tput setaf 1; echo "=> Error: dependency install went wrong"; tput sgr0; exit 1)
elif [ -x "$(command -v pacman)" ]; then
    sudo pacman -S tcl boost boost-libs git cmake make gcc gcc-libs python which python-pip python-pylint || (tput setaf 1; echo "=> Error: dependency install went wrong"; tput sgr0; exit 1)
else
    tput setaf 1
    echo "=> Error: Your distribution is not supported, please install the following packages manually:"
    echo "   - tcl / tcl-dev"
    echo "   - boost / boost-libs"
    echo "   - git"
    echo "   - cmake"
    echo "   - make"
    echo "   - gcc / g++"
    echo "   - python3 / python3-dev"
    echo "   - pylint"
    echo "   - which"
    echo "   - pip"
    tput sgr0
    echo "   and then run this script again. The install will now proceed, but may fail."
fi

echo -e "libclang==16.0.6" > requirements.txt
sudo pip install -r requirements.txt
}


if [ -x "$(command -v plum)" ]; then
    echo -e "\n\nPlum is already installed, skipping dependency installation...\n"
else
    echo -e "\n\nInstalling Plum dependencies...\n\n"
    install_deps
fi

echo -e "\nBuilding Banana Vera++\n\n"

cd /tmp
sudo rm -rf banana-vera/
git clone https://github.com/Epitech/banana-vera.git
cd banana-vera

sed -i 's|add_executable(vera ${srcs})|add_executable(vera ${srcs})\ntarget_compile_options(vera PRIVATE\n  -O3\n  -march=native\n)|g' src/CMakeLists.txt

cmake -B build . -DVERA_LUA=OFF -DPANDOC=OFF -DVERA_USE_SYSTEM_BOOST=ON > /dev/null
cmake --build build -j12 > /dev/null
sudo cp build/src/vera++ /usr/local/bin/



echo -e "\n\nInstalling Plum\n\n"

cd /tmp/Plum

sudo rm -rf /tmp/docker-volume/
mkdir -p /tmp/docker-volume/

echo -e "#!/bin/bash\ncp /usr/local/bin/lambdananas /mounted-dir\ncp -r /usr/local/lib/vera++ /mounted-dir" > /tmp/docker-volume/copy.sh
chmod +x /tmp/docker-volume/copy.sh
sudo docker run --name code-style-tmp -v /tmp/docker-volume:/mounted-dir --entrypoint='/mounted-dir/copy.sh' ghcr.io/epitech/coding-style-checker:latest
sudo docker rm code-style-tmp > /dev/null

sudo cp plum /bin

sudo mkdir -p /opt/plum-coding-style
sudo cp code-style* /opt/plum-coding-style/
sudo cp code_style* /opt/plum-coding-style/
sudo cp VERSION /opt/plum-coding-style/
sudo cp plum_update.sh /opt/plum-coding-style/

sudo cp -r /tmp/docker-volume/vera++ /usr/local/lib
sudo cp /tmp/docker-volume/lambdananas /bin

sudo rm -rf /tmp/docker-volume/
