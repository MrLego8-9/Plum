#!/bin/bash


if [ "$#" == "1" ]; then
  if [ "$1" == "--update-rules" ]; then
    sudo rm -rf /tmp/Plum
    git clone https://github.com/LouisDupraz/Plum.git /tmp/Plum

    echo -e "\nUpdating Rules"

    cd /tmp/Plum || exit 1

    sudo rm -rf /tmp/docker-volume/
    mkdir -p /tmp/docker-volume/

    echo -e "#!/bin/bash\ncp /usr/local/bin/lambdananas /mounted-dir\ncp -r /usr/local/lib/vera++ /mounted-dir" > /tmp/docker-volume/copy.sh
    chmod +x /tmp/docker-volume/copy.sh
    docker run --name code-style-tmp -v /tmp/docker-volume:/mounted-dir --entrypoint='/mounted-dir/copy.sh' ghcr.io/epitech/coding-style-checker:latest
    docker rm code-style-tmp > /dev/null

    sudo cp plum /bin

    sudo mkdir -p /opt/plum-coding-style
    sudo cp code_style* /opt/plum-coding-style/
    sudo cp VERSION /opt/plum-coding-style/
    sudo cp plum_update.sh /opt/plum-coding-style/

    sudo cp -r /tmp/docker-volume/vera++ /usr/local/lib
    sudo cp /tmp/docker-volume/lambdananas /bin

    sudo rm -rf /tmp/docker-volume/
    exit 0
  fi
fi

curr_version="$(cat /opt/plum-coding-style/VERSION)"
upstream_version="$(curl -s https://raw.githubusercontent.com/LouisDupraz/Plum/main/VERSION)"

if [ "$curr_version" != "$upstream_version" ]; then
  printf "Updating Plum\n\n"
  curl https://raw.githubusercontent.com/LouisDupraz/Plum/main/plum_install.sh | bash
  exit 0
else
  printf "Plum is up to date\n"
  exit 0
fi
