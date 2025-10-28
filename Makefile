PY=python

.PHONY: install run dev

install:
	$(PY) -m pip install -r requirements.txt

run:
	uvicorn app.main:app --reload

dev: install run

