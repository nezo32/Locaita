train:
	python src/training.py
metrics:
	tensorboard --logdir=./tensorboard

clear-tensorboard:
	powershell rm tensorboard/*events*
clear-memory-build:
	powershell rm scrapper/*.o, scrapper/*.dll
clear: clear-tensorboard
	powershell rm models/*


build-memory: clear-memory-build memory_scratcher.o
	g++ -shared -o scrapper/MemoryScratcher.dll scrapper/memory_scratcher.o
memory_scratcher.o:
	g++ -c -fPIC scrapper/MemoryScratcher.cpp -o scrapper/memory_scratcher.o
	