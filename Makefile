metrics:
	tensorboard --logdir=./tensorboard

clear-tensorboard:
	powershell rm tensorboard/*events*
clear-memory-build:
	powershell rm dll/*
clear: clear-tensorboard
	powershell rm models/checkpoint*, models/actor*, models/critic*


build-memory: clear-memory-build memory_scratcher.o
	g++ -shared -o dll/MemoryScratcher.dll dll/memory_scratcher.o
memory_scratcher.o:
	g++ -c -fPIC src/memory/MemoryScratcher.cpp -o dll/memory_scratcher.o
	