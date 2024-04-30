play-nomodel: clear
	python neural/main.py
play: clear-train-data
	python neural/main.py --load-models
train: clear-tensorboard
	python neural/train.py
metrics:
	tensorboard --logdir=./tensorboard

clear-tensorboard:
	powershell rm tensorboard/*
clear-train-data:
	powershell rm tmp/*
clear-memory-build:
	powershell rm dll/*
clear: clear-tensorboard clear-train-data
	powershell rm models/*

build-memory: clear-memory-build memory_scratcher.o
	g++ -shared -o dll/MemoryScratcher.dll dll/memory_scratcher.o

memory_scratcher.o:
	g++ -c -fPIC memory/MemoryScratcher.cpp -o dll/memory_scratcher.o
	