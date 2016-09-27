#!/usr/bin/env python
import os
import sys



if(not len(sys.argv) == 2):
	print "Usage: python run_tests.py <file_with_test_names>"
	exit(1)

try:
	test_files = open(sys.argv[1]) 
except:
	print "File with name: " + sys.argv[1] + " doesn't exist!!"
	exit(1)

correct = 0
total_tests = 0
for test_name_newline in test_files.readlines():

	test_name = test_name_newline.rstrip()

	res = os.system("python main.py tests/" + test_name + " > /dev/null 2>&1")	
	if(not res == 0):
		print "Compiler Error at: " + test_name

	res1 = os.system("llc -mtriple=\"x86_64-unknown-gnulinux\" test_asm > /dev/null 2>&1")	
	if(not res1 == 0):
		print "llc Error at: " + test_name
	
	res2 = os.system("clang test_asm.s lib.a -o test_x86 > /dev/null 2>&1")	
	if(not res2 == 0):
		print "Clang Error at: " + test_name

	res3 = os.system("./test_x86 > tests/outputs/" + test_name)	
	if(not res3 == 0):
		print "Execution Error at: " + test_name
	
	if(res+res1+res2+res3 == 0):
		my_output = open("tests/outputs/"+test_name).read()
		expected_output = open("tests/expected_outputs/"+test_name).read()
		if(my_output == expected_output):
			correct += 1
		else:
			print "Wrong output for: " + test_name
	total_tests += 1

print "Correct: " + str(correct) + " out of: " + str(total_tests)
