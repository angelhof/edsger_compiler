#!/usr/bin/env python
import os
import sys
import difflib


old_way = False

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

	test_line = test_name_newline.rstrip().split(" ")
	test_name = test_line[0]
	test_input = None
	if(len(test_line) > 1):
		test_input = test_line[1]


	# Compile cedsg
	res = os.system("python cedsg.py tests/" + test_name + " > /dev/null 2>&1")	
	if(not res == 0):
		print "Compiler Error at: " + test_name

	# Execute test
	if(test_input is not None):
		res3 = os.system("cat tests/" + test_name + ".in | ./a.out > tests/outputs/" + test_name)
	else:
		res3 = os.system("./a.out > tests/outputs/" + test_name)	
	if(not res3 == 0):
		print "Execution Error at: " + test_name
	
	if(res+res3 == 0):
		my_output = open("tests/outputs/"+test_name).read()
		expected_output = open("tests/expected_outputs/"+test_name).read()
		'''Debug Only:
		
		print my_output
		print expected_output
		for i,s in enumerate(difflib.ndiff(my_output, expected_output)):
			if s[0]==' ': 
				continue
			elif s[0]=='-':
				print(u'Delete "{}" from position {}'.format(s[-1],i))
			elif s[0]=='+':
				print(u'Add "{}" to position {}'.format(s[-1],i))  
		'''
		if(my_output == expected_output):
			correct += 1
		else:
			print "Wrong output for: " + test_name
	total_tests += 1


	'''
	TODO: Delete, Old way of running tests
	'''
	if(old_way):
		res = os.system("python cedsg.py tests/" + test_name + " > /dev/null 2>&1")	
		if(not res == 0):
			print "Compiler Error at: " + test_name

		res1 = os.system("llc -mtriple=\"x86_64-unknown-gnulinux\" test_asm > /dev/null 2>&1")	
		if(not res1 == 0):
			print "llc Error at: " + test_name
		
		res2 = os.system("clang test_asm.s lib.a -o test_x86 > /dev/null 2>&1")	
		if(not res2 == 0):
			print "Clang Error at: " + test_name

		if(test_input is not None):
			res3 = os.system("cat tests/" + test_name + ".in | ./test_x86 > tests/outputs/" + test_name)
		else:
			res3 = os.system("./test_x86 > tests/outputs/" + test_name)	
		if(not res3 == 0):
			print "Execution Error at: " + test_name
		
		if(res+res1+res2+res3 == 0):
			my_output = open("tests/outputs/"+test_name).read()
			expected_output = open("tests/expected_outputs/"+test_name).read()
			'''Debug Only:
			
			print my_output
			print expected_output
			for i,s in enumerate(difflib.ndiff(my_output, expected_output)):
				if s[0]==' ': 
					continue
				elif s[0]=='-':
					print(u'Delete "{}" from position {}'.format(s[-1],i))
				elif s[0]=='+':
					print(u'Add "{}" to position {}'.format(s[-1],i))  
			'''
			if(my_output == expected_output):
				correct += 1
			else:
				print "Wrong output for: " + test_name
		total_tests += 1

print "Correct: " + str(correct) + " out of: " + str(total_tests)
