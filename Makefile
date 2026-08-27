.PHONY: compile release test annotate buildext check-isort check-black


cyt:
	cython dreaming_electric_sheep/url.pyx
	cython dreaming_electric_sheep/exceptions.pyx
	cython dreaming_electric_sheep/headers.pyx
	cython dreaming_electric_sheep/cookies.pyx
	cython dreaming_electric_sheep/contents.pyx
	cython dreaming_electric_sheep/messages.pyx
	cython dreaming_electric_sheep/scribe.pyx
	cython dreaming_electric_sheep/baseapp.pyx

compile: cyt
	python3 setup.py build_ext --inplace


clean:
	rm -rf dist/
	rm -rf build/
	rm -f dreaming_electric_sheep/*.c
	rm -f dreaming_electric_sheep/*.so


buildext:
	python3 setup.py build_ext --inplace


annotate:
	cython dreaming_electric_sheep/url.pyx -a
	cython dreaming_electric_sheep/exceptions.pyx -a
	cython dreaming_electric_sheep/headers.pyx -a
	cython dreaming_electric_sheep/cookies.pyx -a
	cython dreaming_electric_sheep/contents.pyx -a
	cython dreaming_electric_sheep/messages.pyx -a
	cython dreaming_electric_sheep/scribe.pyx -a
	cython dreaming_electric_sheep/baseapp.pyx -a


pack:
	DREAMING_ELECTRIC_SHEEP_NO_EXTENSIONS=1 python -m build --sdist


build: test
	python -m build


prepforbuild:
	pip install --upgrade build


testrelease:
	twine upload -r testpypi dist/*


release: clean compile artifacts
	twine upload -r pypi dist/*


test:
	pytest tests/


itest:
	APP_DEFAULT_ROUTER=false pytest itests/


init:
	pip install -r requirements.txt


test-v:
	pytest -v


test-cov-unit:
	pytest --cov-report html --cov=dreaming_electric_sheep tests


test-cov:
	pytest --cov-report html --cov=dreaming_electric_sheep --disable-warnings


lint: check-flake8 check-isort check-black

format:
	@isort dreaming_electric_sheep 2>&1
	@isort tests 2>&1
	@isort itests 2>&1
	@black dreaming_electric_sheep 2>&1
	@black tests 2>&1
	@black itests 2>&1

check-flake8:
	@echo "$(BOLD)Checking flake8$(RESET)"
	@flake8 dreaming_electric_sheep 2>&1
	@flake8 itests 2>&1
	@flake8 tests 2>&1


check-isort:
	@echo "$(BOLD)Checking isort$(RESET)"
	@isort --check-only dreaming_electric_sheep 2>&1
	@isort --check-only tests 2>&1
	@isort --check-only itests 2>&1


check-black:  ## Run the black tool in check mode only (won't modify files)
	@echo "$(BOLD)Checking black$(RESET)"
	@black --check dreaming_electric_sheep 2>&1
	@black --check tests 2>&1
	@black --check itests 2>&1

