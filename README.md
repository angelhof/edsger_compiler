Cutting Edsg
================

This project is a complete edsger compiler in python. It was done for the Compilers course in National Technical University of Athens, Computer and Electrical Engineering department.

Authors
--------
- <a href="https://github.com/angelhof">Konstantinos Kallas</a>
- <a href="https://github.com/etzinis">Eythimios Tzinis</a>

Installation steps
===================

--- Assuming you have python 2 installed ---

Run:
```sh
$ sudo sh install.sh
```
or follow those steps manually:

1) Download and install ply from http://www.dabeaz.com/ply/ply-3.8.tar.gz

2) Download LLVM version 3.4 http://llvm.org/releases/download.html

3) Download Anaconda from http://repo.continuum.io/archive/Anaconda2-4.1.1-Linux-x86_64.sh
-> Run the following command as the normal user
```sh
$ conda install llvmlite
```
to install llvmlite 

To run the tests
=================

Run 
```sh
$ make test
``` 
which runs all the tests in the file tests_to_run and check if they produce the expected output.

To run the compiler
====================

Run 
```sh
$ python cedsg.py tests/"$1"
$ ./a.out
```

Preparation
============
Set the llvm mtriple in the beginning of gile cedsg.py with your specific triple in order to run the tests.

The default one is "x86_64-unknown-linux-gnu" 
[Supported Triples](http://llvm.org/docs/CodeGenerator.html#x86-target-triples-supported)

 
