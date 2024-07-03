#!/bin/bash
sudo rm -rf /tmp/Plum
git clone https://github.com/MrLego8-9/Plum.git /tmp/Plum

function install_deps() {
if [ -x "$(command -v dnf)" ]; then
    sudo dnf install -y tcl-devel boost-devel git cmake make gcc-c++ python3-devel which python3-pylint python3-clang clang docker || (echo "=> Error: dependency install went wrong"; exit 1)
elif [ -x "$(command -v apt-get)" ]; then
    sudo apt-get -y install tcl-dev libboost-all-dev git cmake make build-essential python3-dev libpython3-dev pylint python3-clang clang docker || (echo "=> Error: dependency install went wrong"; exit 1)
elif [ -x "$(command -v pacman)" ]; then
    sudo pacman -S --noconfirm tcl boost boost-libs git cmake make gcc gcc-libs python which python-pylint clang docker || (echo "=> Error: dependency install went wrong"; exit 1)
else
    echo "=> Error: Your distribution is not supported, please install the following packages manually:"
    echo "   - tcl / tcl-dev"
    echo "   - boost / boost-libs"
    echo "   - git"
    echo "   - cmake"
    echo "   - make"
    echo "   - gcc / g++"
    echo "   - clang"
    echo "   - python3 / python3-dev"
    echo "   - pylint"
    echo "   - python3-clang"
    echo "   - which"
    echo "   - pip"
    echo "   and then run this script again. The install will now proceed, but may fail."
fi
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

sed -i 's|add_executable(vera ${srcs})|add_executable(vera ${srcs})\ntarget_compile_options(vera PRIVATE\n  -Ofast\n  -march=native\n)\ntarget_link_options(vera PRIVATE\n  -flto=auto\n)|g' src/CMakeLists.txt

cmake -B build . -DVERA_LUA=OFF -DPANDOC=OFF -DVERA_USE_SYSTEM_BOOST=ON > /dev/null
cmake --build build -j12 > /dev/null
sudo cp build/src/vera++ /usr/local/bin/



echo -e "\n\nInstalling Plum\n\n"

cd /tmp/Plum

sudo systemctl start docker

sudo rm -rf /tmp/docker-volume/
mkdir -p /tmp/docker-volume/

echo -e "#!/bin/bash\ncp /usr/local/bin/lambdananas /mounted-dir\ncp -r /usr/local/lib/vera++ /mounted-dir" > /tmp/docker-volume/copy.sh
chmod +x /tmp/docker-volume/copy.sh
sudo docker pull ghcr.io/epitech/coding-style-checker:latest
sudo docker run --name code-style-tmp -v /tmp/docker-volume:/mounted-dir --entrypoint='/mounted-dir/copy.sh' ghcr.io/epitech/coding-style-checker:latest
sudo docker rm code-style-tmp > /dev/null

sudo cp -r /tmp/docker-volume/vera++ /usr/local/lib
sudo cp /tmp/docker-volume/lambdananas /bin
sudo rm -f /bin/plum

if [ -x "$(command -v go)" ]; then
    echo -e "Go is installed, compiling plum"
    go build -tags netgo
else
    echo -e "Go is not installed, downloading prebuilt release"
    wget -O "/tmp/Plum/plum" "https://github.com/MrLego8-9/Plum/releases/latest/download/plum"
fi
sudo cp /tmp/Plum/plum /bin/plum

sudo rm -rf /tmp/docker-volume/
