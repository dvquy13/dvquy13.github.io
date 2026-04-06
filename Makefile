.PHONY: run build validate analytics analytics-push fetch-metrics
.ONESHELL:

run:
	quarto preview --host 0.0.0.0 --port 8183

build:
	bash scripts/check-quarto-version.sh
	quarto render
	bash scripts/validate-rss.sh

validate:
	bash scripts/validate-rss.sh

fetch-metrics:
	gh workflow run fetch-metrics.yml
	@sleep 3
	gh run watch $$(gh run list --workflow=fetch-metrics.yml --limit=1 --json databaseId -q '.[0].databaseId') --exit-status

analytics:
	cd analytics && \
		uv run scripts/fetch-metrics.py > /tmp/dvq-ga4-metrics.json ; \
		uv run scripts/fetch-giscus-reactions.py > /tmp/dvq-giscus-metrics.json ; \
		uv run scripts/fetch-posts-published.py > /tmp/dvq-posts-metrics.json ; \
		python3 scripts/display-dashboard.py /tmp/dvq-ga4-metrics.json /tmp/dvq-giscus-metrics.json /tmp/dvq-posts-metrics.json

analytics-push:
	cd analytics && \
		uv run scripts/fetch-metrics.py > /tmp/dvq-ga4-metrics.json && \
		uv run scripts/fetch-giscus-reactions.py > /tmp/dvq-giscus-metrics.json && \
		uv run scripts/fetch-posts-published.py > /tmp/dvq-posts-metrics.json && \
		python3 -c "\
import json; \
ga4=json.load(open('/tmp/dvq-ga4-metrics.json')); \
gi=json.load(open('/tmp/dvq-giscus-metrics.json')); \
po=json.load(open('/tmp/dvq-posts-metrics.json')); \
merged={**ga4,'metrics':{**ga4['metrics'],**gi['metrics'],**po['metrics']}}; \
print(json.dumps(merged)) \
		" | uv run scripts/push-and-notify.py
