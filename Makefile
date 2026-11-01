PYTHONPATH := packages/oie_core/src

.PHONY: check test sample sample-operations

check:
	@PYTHONPATH=$(PYTHONPATH) python -m compileall -q packages/oie_core/src scripts
	@PYTHONPATH=$(PYTHONPATH) python -m pytest -q packages/oie_core/tests

test:
	@PYTHONPATH=$(PYTHONPATH) python -m pytest -q packages/oie_core/tests

sample:
	@PYTHONPATH=$(PYTHONPATH) python scripts/analyze_sample.py

sample-operations:
	@PYTHONPATH=$(PYTHONPATH) python scripts/analyze_operations.py
