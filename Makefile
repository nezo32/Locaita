.PHONY: train

train:
	python src/training.py
metrics:
	tensorboard --logdir=./tensorboard

clear-tensorboard:
	powershell rm tensorboard/*events*
clear: clear-tensorboard
	powershell rm models/*

# C++ compile/clear
build-memory: clear-memory-build scrapper/memory_scratcher.dll
scrapper/memory_scratcher.dll: scrapper/memory_scratcher.o
	g++ -shared -o $@ $^
scrapper/memory_scratcher.o: scrapper/MemoryScratcher.cpp
	g++ -c -fPIC $< -o $@
clear-memory-build:
	powershell rm scrapper/*.o, scrapper/*.dll