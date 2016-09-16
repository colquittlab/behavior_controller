#!/bin/bash
#!/bin/bash


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
if $DOPACKAGES
then
    # install existing packages
    APTPACKAGES="python-scipy python-alsaaudio ntp  libopencv-dev python-opencv"
    PIPPACKAGES="pyserial ipython schedule ino"
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
    read -p "Do you wish to set the timezone? [Y/N] " yn
    case $yn in
        [Yy]* ) DOTZ=true;  break;;
        [Nn]* ) DOTZ=false; break;;
    esac
done
if $DOTZ
then
    dpkg-reconfigure tzdata
fi


while true; do
    read -p "Do you wish to install automatic screen invocation for root? [Y/N] " yn
    case $yn in
        [Yy]* ) DOSCREEN=true;  break;;
        [Nn]* ) DOSCREEN=false; break;;
    esac
done
if $DOSCREEN
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
# mkdir /data
# mkdir /data/stimuli
# mkdir /data/behavior
# chmod -R 777 /data













