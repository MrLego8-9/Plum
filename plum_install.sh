#!/bin/bash
sudo rm -rf /tmp/Plum
git clone https://github.com/LouisDupraz/Plum.git /tmp/Plum

echo -e "\nBuilding Banana Vera++\n\n"

cd /tmp
sudo rm -rf banana-vera/
git clone https://github.com/Epitech/banana-vera.git
cd banana-vera

if [ -f /bin/dnf ]; then
  sudo dnf install -y tcl-devel boost-devel git cmake make gcc-c++ python3-devel which
  echo -e "pylint==2.17.5\nlibclang==16.0.6" > requirements.txt
  sudo pip install -r requirements.txt
fi

boost_version=$(cat src/boost.cmake | grep "set(Boost_VERSION " | cut -d' ' -f4 | sed 's/)//g')
boost_mirror=$(cat src/boost.cmake | grep "set(BOOST_MIRROR" | cut -d' ' -f4)
new_boost_mirror=$(echo $boost_mirror | sed "s|$boost_mirror|netcologne.dl.sourceforge.net|g")
boost_url=$(cat src/boost.cmake | grep "set(Boost_URL " | cut -d'"' -f2)
boost_file="boost_$(echo "$boost_version" | tr '.' '_').tar.bz2"
new_boost_url=$(echo 'https://${BOOST_MIRROR}/project/boost/boost/'"$boost_version/$boost_file")
sed -i "s|$boost_mirror|$new_boost_mirror|g" src/boost.cmake
sed -i "s|$boost_url|$new_boost_url|g" src/boost.cmake

cmake -B build . -DVERA_LUA=OFF -DPANDOC=OFF -DVERA_USE_SYSTEM_BOOST=ON > /dev/null
cmake --build build -j12 > /dev/null
sudo cp build/src/vera++ /usr/local/bin/



echo -e "\n\nInstalling Plum\n\n"

cd /tmp/Plum

sudo rm -rf /tmp/docker-volume/
mkdir -p /tmp/docker-volume/

echo -e "#!/bin/bash\ncp /usr/local/bin/lambdananas /mounted-dir\ncp -r /usr/local/lib/vera++ /mounted-dir" > /tmp/docker-volume/copy.sh
chmod +x /tmp/docker-volume/copy.sh
docker run --name code-style-tmp -v /tmp/docker-volume:/mounted-dir --entrypoint='/mounted-dir/copy.sh' ghcr.io/epitech/coding-style-checker:latest
docker rm code-style-tmp > /dev/null

sudo cp plum /bin

sudo mkdir -p /opt/plum-coding-style
sudo cp code-style* /opt/plum-coding-style/
sudo cp code_style* /opt/plum-coding-style/
sudo cp VERSION /opt/plum-coding-style/
sudo cp plum_update.sh /opt/plum-coding-style/

sudo cp -r /tmp/docker-volume/vera++ /usr/local/lib
sudo cp /tmp/docker-volume/lambdananas /bin

sudo rm -rf /tmp/docker-volume/
