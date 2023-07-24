.PHONY: default install build

default: test

install:
	poetry install

build:
	poetry run maturin develop

build-prod:
	poetry run maturin build

#test: build
#	poetry run pytest -s pytest/*

test:
	poetry run pytest -s tests/*