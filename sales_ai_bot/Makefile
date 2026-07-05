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
	rm -rf allure-results

test-allure:
	pytest tests/test_frontend.py --alluredir=allure-results --screenshot=on --video=on -v

allure-serve:
	allure serve allure-results