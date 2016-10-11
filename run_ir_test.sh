#!/bin/bash

python main.py ./tests/$1.eds &&
llc -O2 -mtriple="x86_64-unknown-gnulinux" test_asm &&
echo "Clang" &&
clang -O2 test_asm.s lib.a -o test_x86 &&
echo "Program Output" &&
./test_x86 

