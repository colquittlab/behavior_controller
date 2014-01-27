#!/bin/bash

PROJECT_NAME=brainard_dev


# do stuff to install pip
# do stuff to install needed non-python packages

# Iterate over the python packages needed to bootstrap a working environment
pythonpackages=("virtualenv")
for package in ${pythonpackages[*]}
do
    if [ `which $package`  ]; then
        echo "Found $package, no need to install"
    else
        echo "$package not found, installing (might ask for root for pip):"
        sudo pip install $package || { echo "$package failed to easy_install, non-zero exit status returned" ; return 1; }
    fi
done
# these ones need .sh for the which test
pythonpackages=("virtualenvwrapper" "virtualenv-clone")
for package in ${pythonpackages[*]}
do
    if [ `which ` $package `.sh`  ]; then
        echo "Found $package, no need to install"
    else
        echo "$package not found, installing (might ask for root for pip):"
        sudo pip install $package || { echo "$package failed to easy_install, non-zero exit status returned" ; return 1; }
    fi
done
# source from active virtualenvwrapper
source `which virtualenvwrapper.sh`

# Determine if the virtualenv exists
if [ -d ~/.virtualenvs/$PROJECT_NAME ]; then
    echo "virtualenv $PROJECT_NAME already exists, not making another one"
else
    mkvirtualenv $PROJECT_NAME || source `which virtualenvwrapper.sh`; mkvirtualenv $PROJECT_NAME || { echo "mkvirtualenv failed, reopen a new shell and rerun the script" ; return 1; }
fi


# install non-python dependencies for matplotlib


# activatae virtual enviroment
workon $PROJECT_NAME || { echo "virtualenvwrapper failed to workon $PROJECT_NAME, non-zero exit status returned" ; return 1; }

# now install the angry python libs
pip install -q numpy
pip install -q scipy
pip install -q matplotlib

# Install remaining packages as needed, pip handles the logic here
pip install -qr requirements.txt 2>&1 > pip.log

echo "dependencies installed, activating environment"
add2virtualenv .


