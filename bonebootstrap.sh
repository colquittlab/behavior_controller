#!/bin/bash

# set hostname
while true; do
    read -p "Do you wish to set the hostname? [Y/N] " yn
    case $yn in
        [Yy]* ) read -p "Enter new hostname" hn; hostname -v -b $hn; break;;
        [Nn]* ) break;;
    esac
done

# set password for root
while true; do
    read -p "Do you wish to set password for root? [Y/N] (you should!!)  " yn
    case $yn in
        [Yy]* ) echo "set password for root"; passwd root; break;;
        [Nn]* ) break;;
    esac
done
# create users as desired
while true; do
    read -p "Do you wish to make a new (sudo) user? [Y/N]  " yn
    case $yn in
        [Yy]* ) read -p "Enter User name\n" un; adduser $un --ingroup sudo;;
        [Nn]* ) break;;
    esac
done

# # setup eth0 interface
# while true; do
#     read -p "Do you wish to setup eth0 as static ip? [Y/N]  " yn
#     case $yn in
#         [Yy]* ) read -p "Enter address" staticaddress;
#                 netmask=255.255.254.0;
#                 gateway=169.230.190.1;
#                 dnsnameservers=169.230.190.10;
#                 dnssearch=cin.ucsf.edu;
#                 awk -f lib/changeInterface.awk /etc/network/interfaces device=eth0 adress=$staticaddress netmask=$netmask gateway=$gateway
#                 break;;
#         [Nn]* ) break;;
#     esac
# done
# exit
# # setup usb0 interface



while true; do
    read -p "Do you wish to update all required packages [Y/N] " yn
    case $yn in
        [Yy]* ) DOPACKAGES=true;  break;;
        [Nn]* ) DOPACKAGES=false; break;;
    esac
done
if [ "$DOPACKAGES" ]
then
    # install existing packages
    APTPACKAGES="python-scipy python-alsaaudio"
    PIPPACKAGES="pyexecjs pyserial Adafruit-BBIO ipython"
    apt-get update
    for PACK in $APTPACKAGES
    do
        apt-get --assume-yes install $PACK
    done

    for PACK in $PIPPACKAGES
    do
        sudo pip install $PACK --upgrade
    done
fi

while true; do
    read -p "Do you wish to install automatic screen invocation for root? [Y/N] " yn
    case $yn in
        [Yy]* ) DOSCREEN=true;  break;;
        [Nn]* ) DOSCREEN=false; break;;
    esac
done
if [ "$DOSCREEN" ]
then
    # install screen script
    if  grep -q "# Auto-screen invocation" ~/.bashrc
    then
        echo "screen invocation in bash script already"
    else
        echo "adding screen invocation to bash script"
        cat lib/screen_invocation_script >> ~/.bashrc
    fi
fi

# make data directories (if they don't already exist) and set permissions
mkdir /data
mkdir /data/stimuli
mkdir /data/behavior
chmod -R 777 /data

