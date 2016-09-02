Installation steps
===================

--- Assuming you have python 2 installed ---

Either run
```sh
$ make install
```
while having root priviledges 

or if you don't like Makefiles do the following:

1) Download and install ply from http://www.dabeaz.com/ply/ply-3.8.tar.gz

2) Download LLVM version 3.4 http://llvm.org/releases/download.html

3) Download Anaconda from http://repo.continuum.io/archive/Anaconda2-4.1.1-Linux-x86_64.sh
-> Run 
```sh
$ conda install llvmlite
```
to install llvmlite 

To run the tests
================

Either run 
```sh
$ ./run_tests.py
``` 
which runs all the tests in the test folder and prints their output in files in output

or run
```sh
$ python main.py <input_file_name> [output_file_name]
```
	


 
