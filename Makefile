.PHONY:
.ONESHELL:

run:
	quarto preview --host 0.0.0.0 --port 8183

build:
	quarto render
