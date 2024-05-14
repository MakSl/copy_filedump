.PHONY: test
test:
	pytest

.PHONY: fmt
fmt:
	ruff format

.PHONY: lint
lint:
	ruff check