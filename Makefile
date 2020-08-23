.PHONY: test help pylint 

all: help

help:
	@echo "available targets:"
	@echo "help             :    print this help message"
	@echo "pylint           :    run pylint"
	@echo "test             :    run all unit tests"
	@echo "requirements.txt :    create requirements.txt"

requirements.txt: 
	pipenv run pip freeze > requirements.txt

pylint:
	pipenv run pylint foozzer.py

test:
	pipenv run python -m unittest discover -v

