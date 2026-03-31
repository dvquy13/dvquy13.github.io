.PHONY:
.ONESHELL:

run:
	quarto preview --host 0.0.0.0 --port 8183

build:
	bash scripts/check-quarto-version.sh
	quarto render
	bash scripts/validate-rss.sh

validate:
	bash scripts/validate-rss.sh
