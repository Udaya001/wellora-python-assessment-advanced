.PHONY: up down test seed lint clean logs

up:
	docker-compose up -d

down:
	docker-compose down

test:
	python -m pytest tests/ -v --cov=app --cov-report=html --cov-report=term-missing

seed:
	@echo "Seed script not implemented yet. Create a script in scripts/seed.py and update this target."

lint:
	@echo "Linting not configured yet. Add ruff/flake8 commands here."

clean:
	docker-compose down -v

logs:
	docker-compose logs -f api