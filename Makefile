.PHONY: install dev test evaluate lint format docker-up docker-down clean

install:
	cd backend && pip install -r requirements.txt
	cd frontend && npm install

dev:
	# Start backend and frontend in parallel
	cd backend && uvicorn app.main:app --reload --port 8000 &
	cd frontend && npm run dev

test:
	cd backend && pytest tests/ -v --cov=app

evaluate:
	cd backend && python -m evaluation.scripts.run_ci_evaluation \
		--dataset ../evaluation/datasets/sample_eval.json \
		--output ../evaluation/reports/latest.json

lint:
	cd backend && python -m flake8 app/ tests/ --max-line-length=120
	cd frontend && npm run lint

format:
	cd backend && python -m black app/ tests/
	cd frontend && npm run lint -- --fix

docker-up:
	docker compose up --build

docker-down:
	docker compose down -v

clean:
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -name "*.pyc" -delete
	cd frontend && rm -rf dist node_modules/.cache
