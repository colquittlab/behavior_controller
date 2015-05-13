#!/bin/bash

APTPACKAGES="python-scipy"
PIPPACKAGES="pyexecjs serial"
apt-get update

for PACK in $APTPACKAGES
do
    apt-get --assume-yes install $PACK
done

for PACK in $PIPPACKAGES
do
    sudo pip install $PACK --upgrade
done
