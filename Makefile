## Please read README first
.PHONY: test clean distclean prepare


compiler: staticlib doublefun
	echo "Fill 1. make the edsger lib 2. make the c part about doubles"
	

staticlib: src/thy_kos_new_delete.c
	gcc -c src/thy_kos_new_delete.c -o obj/thy_kos_new_delete.o
	ar rcs obj/libnew.a obj/thy_kos_new_delete.o

doublefun: src/thy_kos_strold.c
	gcc -fPIC -shared -o obj/libstrtold.so src/thy_kos_strold.c

test: 
	python run_tests.py tests_to_run

prepare:
	sudo sh install.sh

clean:
	echo "Fill"

distclean:
	echo "Fill"	