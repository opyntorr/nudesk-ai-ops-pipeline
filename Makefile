.PHONY: help install test run tunnel docker-up docker-down clean

VENV := .venv
PYTHON := $(shell if [ -f $(VENV)/bin/python ]; then echo $(VENV)/bin/python; else echo python3; fi)
PIP := $(shell if [ -f $(VENV)/bin/pip ]; then echo $(VENV)/bin/pip; else echo pip; fi)
STREAMLIT := $(shell if [ -f $(VENV)/bin/streamlit ]; then echo $(VENV)/bin/streamlit; else echo streamlit; fi)

help:
	@echo "nuDesk Operations Studio - Developer Commands"
	@echo "------------------------------------------------------"
	@echo "make install     : Install all project dependencies into active environment"
	@echo "make test        : Run full automated test suite"
	@echo "make run         : Launch Streamlit web application on port 8501"
	@echo "make tunnel      : Start secure Cloudflare HTTPS tunnel for mobile demo"
	@echo "make docker-up   : Spin up local n8n workflow automation container"
	@echo "make docker-down : Stop local n8n container"
	@echo "make clean       : Remove temporary bytecode and cache directories"

install:
	$(PIP) install -r requirements.txt

test:
	$(PYTHON) -m unittest discover -s tests -p "test_*.py" -v

run:
	$(STREAMLIT) run app.py --server.port 8501

tunnel:
	./scripts/start_tunnel.sh

docker-up:
	docker compose up -d

docker-down:
	docker compose down

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
