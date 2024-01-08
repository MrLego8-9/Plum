#!/bin/bash

curr_version=$(cat /opt/plum-coding-style/VERSION)
upstream_version=$(curl -s https://raw.githubusercontent.com/LouisDupraz/Plum/main/VERSION)

if [ "$curr_version" != "$upstream_version" ]; then
  echo -e "Updating Plum\n\n"
  curl https://raw.githubusercontent.com/LouisDupraz/Plum/main/plum_install.sh | bash
else
  echo -e "Plum is up to date\n\n"
fi