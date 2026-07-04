.PHONY: test test-cov test-slow

test:
	pytest -v

test-cov:
	pytest --cov=app --cov-report=term-missing --cov-report=html

test-slow:
	pytest -v -m "not slow"

clean:
	rm -rf htmlcov
	rm -rf .pytest_cache
	rm -rf .coverage
	