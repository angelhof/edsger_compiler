#!/usr/bin/env python
import os

current = os.getcwd()

total_tests = len(os.listdir(current + "/tests/"))
correct = 0

for input_file in os.listdir(current + "/tests/"):
	input_path = current + "/tests/" + input_file
	a = os.system("python main.py tests/" + input_file  + " outputs/" + input_file.split('.')[0] + ".out")	
	if(a == 0):
		correct += 1
	else:
		print "Error at: " + input_file

print "Correct: " + str(correct) + " out of: " + str(total_tests)
print "You can see pretty ASTs in the outputs folder :)"
