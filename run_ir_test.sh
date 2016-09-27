#!/bin/bash

python main.py ./tests/$1.eds &&
llc -mtriple="x86_64-unknown-gnulinux" test_asm &&
echo "Clang" &&
clang test_asm.s lib.a -o test_x86 &&
echo "Program Output" &&
./test_x86 

