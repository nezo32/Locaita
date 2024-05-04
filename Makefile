play-init: clear build-memory
	python src/main.py
play: clear-train-data
	python src/main.py --load-models
train: clear-tensorboard
	python src/train.py
metrics:
	tensorboard --logdir=./tensorboard

clear-tensorboard:
	powershell rm tensorboard/*events*
clear-train-data:
	powershell rm tmp/*.npy
clear-memory-build:
	powershell rm dll/*
clear: clear-tensorboard clear-train-data
	powershell rm models/checkpoint*, models/actor*, models/critic*


build-memory: clear-memory-build memory_scratcher.o
	g++ -shared -o dll/MemoryScratcher.dll dll/memory_scratcher.o
memory_scratcher.o:
	g++ -c -fPIC src/memory/MemoryScratcher.cpp -o dll/memory_scratcher.o
	