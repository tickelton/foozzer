.PHONY: test help pylint run

all: help

help:
	@echo "available targets:"
	@echo "help             :    print this help message"
	@echo "pylint           :    run pylint"
	@echo "mypy             :    run mypy"
	@echo "test             :    run all unit tests"
	@echo "requirements.txt :    create requirements.txt"
	@echo "run              :    example of all required arguments"

requirements.txt: 
	pipenv run pip freeze > requirements.txt

pylint:
	pipenv run pylint foozzer.py

mypy:
	pipenv run mypy foozzer.py

test:
	pipenv run python -m unittest discover -v

run:
	pipenv run python foozzer.py -v -v -v  -i D:\Workspace\tmp\in -o D:\Workspace\tmp\out -D "C:\Program Files (x86)\Dr. Memory\bin" -m fpl_basic -r foobar2k -- -F "C:\Program Files (x86)\foobar2000" -R D:\Workspace\foozzer\images
