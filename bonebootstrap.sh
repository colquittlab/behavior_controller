#!/bin/bash

# set password for root
passwd root
# create users as desired
while true; do
    read -p "Do you wish to make a new (sudo) user? [Y/N]" yn
    case $yn in
        [Yy]* ) read -p "Enter User name" un; adduser $un --ingroup sudo; passwd $un; break;;
        [Nn]* ) exit;;
    esac
done





APTPACKAGES="python-scipy python-alsaaudio"
PIPPACKAGES="pyexecjs pyserial"
apt-get update

for PACK in $APTPACKAGES
do
    apt-get --assume-yes install $PACK
done

for PACK in $PIPPACKAGES
do
    sudo pip install $PACK --upgrade
done
