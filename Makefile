.PHONY: dev install install-py

dev: ## Start FastAPI server + Vue dev server (Ctrl+C stops both)
	@bash -c 'trap "kill 0" EXIT; .venv/bin/uvicorn api:app --reload --port 8000 & npm --prefix client run dev'

install: install-py ## Install all dependencies
	npm --prefix client install

install-py: ## Install Python dependencies into .venv
	uv venv --quiet && uv pip install -r requirements.txt --quiet
