#!/bin/bash

# set password for root
while true; do
    read -p "Do you wish to set password for root? [Y/N] (you should!!)\n" yn
    case $yn in
        [Yy]* ) echo "set password for root"; passwd root;;
        [Nn]* ) exit;;
    esac
done
# create users as desired
while true; do
    read -p "Do you wish to make a new (sudo) user? [Y/N]\n" yn
    case $yn in
        [Yy]* ) read -p "Enter User name\n" un; adduser $un --ingroup sudo; passwd $un;;
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
