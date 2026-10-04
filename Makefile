PYTHON ?= python3
.PHONY: setup analyze test dashboard
setup:
	$(PYTHON) -m pip install -r requirements.txt
analyze:
	$(PYTHON) experiment.py
test:
	$(PYTHON) -m unittest discover -v
dashboard:
	streamlit run app.py
