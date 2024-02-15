#!/bin/bash

if [ "$#" == "1" ]; then
  if [ "$1" == "--update-rules" ]; then
    sudo rm -rf /tmp/banana-coding-style-checker
    sudo rm -rf /tmp/lambdananas
    cd /tmp
    git clone https://github.com/Epitech/banana-coding-style-checker.git
    sudo mv banana-coding-style-checker/vera /usr/local/lib/vera++

    git clone https://github.com/Epitech/lambdananas.git
    cd lambdananas
    make

    sudo cp lambdananas /bin
    sudo rm -rf /tmp/banana-coding-style-checker
    sudo rm -rf /tmp/lambdananas
  fi
fi