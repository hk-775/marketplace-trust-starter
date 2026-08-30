.PHONY: demo test validate site site-check

demo:
	./scripts/demo.sh

test:
	./scripts/test.sh

validate:
	./scripts/validate.sh

site:
	python scripts/build_site.py

site-check:
	python scripts/build_site.py --check

