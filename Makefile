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
#	-rstcheck docs/index.rst

lint:
	-pylint pysmithchart/smithaxes.py
	-pylint pysmithchart/smithhelper.py
	-pylint tests/test_xy_to_z.py
	-pylint tests/test_schang.py
	-pylint tests/test_noergaard.py
	-pylint tests/test_simple.py
	-pylint tests/test_vmeijin_short.py
	-pylint tests/test_vmeijin_full.py

rcheck:
	make clean
	black .
	ruff check .
	make rstcheck
	pyroma -d .
	check-manifest
#	make notecheck
#	make html
	make test

test:
	pytest -v tests/test_xy_to_z.py
	pytest -v tests/test_schang.py
	pytest -v tests/test_noergaard.py
	pytest -v tests/test_simple.py
	pytest -v tests/test_vmeijin_short.py
	pytest -v tests/test_vmeijin_full.py

clean:
	rm -rf dist
	rm -rf .DS_Store
	rm -rf pysmithchart.egg-info
	rm -rf pysmithchart/__pycache__
	rm -rf tests/__pycache__
	rm -rf tests/.ipynb_checkpoints
	rm -rf tests/.DS_Store
	rm -rf build
	rm -rf .ruff_cache
	rm -rf .pytest_cache
	rm -rf tests/charts/*

realclean:
	make clean

.PHONY: clean html test realclean \
        rcheck doccheck lintcheck rstcheck notecheck