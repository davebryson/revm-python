.PHONY: default install build, create-mitre

default: test

install:
	poetry install

build:
	poetry run maturin develop

build-prod:
	poetry run maturin build

test-pub:
	poetry run maturin publish -r testpypi

#test: build
#	poetry run pytest -s pytest/*

test:
	poetry run pytest -s tests/*
