#!/bin/bash

# set password for root
while true; do
    read -p "Do you wish to set password for root? [Y/N] (you should!!)  " yn
    case $yn in
        [Yy]* ) echo "set password for root"; passwd root; break;;
        [Nn]* ) exit;;
    esac
done
# create users as desired
while true; do
    read -p "Do you wish to make a new (sudo) user? [Y/N]  " yn
    case $yn in
        [Yy]* ) read -p "Enter User name\n" un; adduser $un --ingroup sudo;;
        [Nn]* ) exit;;
    esac
done
echo "hello"


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
