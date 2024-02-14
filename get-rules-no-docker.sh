#!/bin/bash

if [ "$#" == "1" ]; then
  if [ "$1" == "--update-rules" ]; then
    cd /tmp
    git clone https://github.com/Epitech/banana-coding-style-checker.git
    sudo mv banana-coding-style-checker/vera /usr/local/lib/vera++

    git clone https://github.com/Epitech/lambdananas.git
    cd lambdananas
    make

    sudo cp lambdananas /bin
  fi
fi