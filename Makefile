## Please read README first
.PHONY: test clean distclean prepare


compiler:
	echo "Fill 1. make the edsger lib 2. make the c part about doubles"

test: 
	python run_tests.py tests_to_run

prepare:
	sudo sh install.sh

clean:
	echo "Fill"

distclean:
	echo "Fill"	