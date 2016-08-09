## Please read README first

install: ply-3.8/setup.py llvmlite
	cd ./ply-3.8; sudo python setup.py install
	sudo apt-get install build-essential llvm

ply-3.8/setup.py: ply-3.8.tar.gz
	tar -xvzf ply-3.8.tar.gz; rm ply-3.8.tar.gz

ply-3.8.tar.gz:
	wget http://www.dabeaz.com/ply/ply-3.8.tar.gz

llvmlite: 
	wget http://repo.continuum.io/archive/Anaconda2-4.1.1-Linux-x86_64.sh
	bash Anaconda2-4.1.1-Linux-x86_64.sh; gnome-shell --replace; conda install llvmlite

clean:
	rm -f Anaconda2-4.1.1-Linux-x86_64.sh ply-3.8.tar.gz
