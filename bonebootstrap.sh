#!/bin/bash

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


# install existing packages
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

# download and install latest adafruit_gpio


# install screen script
TEST=`~/.bashrc | grep "# Auto-screen invocation" -q`
if [ $TEST ]
then
    echo "screen invocation in bash script already"
else
    echo "adding screen invocation to bash script"
    cat lib/screen_invocation_script >> ~/.bashrc
end
done




# make data directories (if they don't already exist)
mkdir /root/data
mkdir /root/data/stimuli
mkdir /root/data/behavior


