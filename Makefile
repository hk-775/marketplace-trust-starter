.PHONY: browser-check check coverage demo history-scan lint package-check scan site site-check sync test validate

sync:
	uv sync --locked --python 3.12

demo:
	./scripts/demo.sh

test:
	./scripts/test.sh

coverage:
	uv run --locked pytest --cov --cov-report=term-missing

lint:
	uv run --locked ruff check src tests scripts tools

scan:
	uv run --locked python tools/repo_scan.py --pretty

history-scan:
	uv run --locked python tools/history_scan.py --pretty

browser-check:
	uv run --locked python tools/browser_check.py

package-check:
	uv run --locked python tools/package_check.py

validate:
	./scripts/validate.sh

site:
	uv run --locked python scripts/build_site.py

site-check:
	uv run --locked python scripts/build_site.py --check

check: lint coverage site-check scan history-scan browser-check package-check
