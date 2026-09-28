.PHONY: setup run-backend run-frontend test seed cost-report clean

setup:
	python -m pip install --upgrade pip
	cd backend && pip install -r requirements.txt
	cd frontend && npm install

run-backend:
	cd backend && uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

run-frontend:
	cd frontend && npm run dev

test:
	cd backend && pytest -v

seed:
	cd backend && python scripts/seed_demo.py

cost-report:
	cd backend && python scripts/cost_report.py

clean:
	rm -rf data/*.db data/logs/*.log data/uploads/* data/artifacts/*
