.PHONY: dev install

dev: ## Start API server + Vue dev server (Ctrl+C stops both)
	@bash -c 'trap "kill 0" EXIT; python3 server.py & npm --prefix client run dev'

install: ## Install client dependencies (Python needs none)
	npm --prefix client install
