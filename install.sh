#!/bin/bash

# The following script installs the compiler dependencies
# WARNING: It should be run with administration priviledges

# Note: Assuming apt-get, python, tar commands
#  				 and Linux x86_64 

# 1. Download and setup ply
wget http://www.dabeaz.com/ply/ply-3.8.tar.gz
tar -xvzf ply-3.8.tar.gz
rm ply-3.8.tar.gz
cd ./ply-3.8
python setup.py install
cd ../

# 2. Download and setup Anaconda
wget http://repo.continuum.io/archive/Anaconda2-4.1.1-Linux-x86_64.sh
bash Anaconda2-4.1.1-Linux-x86_64.sh
sh

# 3. Install llvmlite
conda install llvmlite

# 4. Install llvm
apt-get install build-essential llvm