#!/bin/bash

python main.py ./tests/ir_test_$1.eds &&
llc -mtriple="x86_64-unknown-gnulinux" test_asm &&
clang test_asm.s lib.a -o test_x86 &&
echo "Program Output" &&
./test_x86

