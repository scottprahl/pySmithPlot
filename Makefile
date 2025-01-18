SPHINXOPTS    ?=
SPHINXBUILD   ?= sphinx-build
SOURCEDIR     = docs
BUILDDIR      = docs/_build

default:
	@echo Type: make rcheck, make html, or make clean

html:
	$(SPHINXBUILD) -b html "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS)
	open docs/_build/index.html

notecheck:
	make clean
	python -m pytest --verbose --notebooks tests/test_all_notebooks.py
	rm -rf __pycache__

rstcheck:
	-rstcheck README.rst
	-rstcheck CHANGELOG.rst
	-rstcheck docs/index.rst

lint:
	-pylint pysmithplot/smithaxes.py
	-pylint pysmithplot/smithhelper.py
	-pylint tests/smith_full_test.py
	-pylint tests/smith_short_test.py

doccheck:
	-ruff check miepython/miepython.py

rcheck:
	make notecheck
	make rstcheck
	make lintcheck
	make doccheck
	- flake8 .
	pyroma -d .
	check-manifest
	make html
	make test

test:
	python tests/smith_short_test.py
	python tests/smith_full_test.py

clean:
	rm -rf dist
	rm -rf pysmithplot.egg-info
	rm -rf pysmithplot/__pycache__
	rm -rf tests/__pycache__
	rm -rf tests/.ipynb_checkpoints
	rm -rf build
	rm -rf .ruff_cache
	rm -rf .pytest_cache

realclean:
	make clean

.PHONY: clean html test realclean \
        rcheck doccheck lintcheck rstcheck notecheck