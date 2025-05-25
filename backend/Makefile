run:
	@export $$(cat .env | xargs) && uvicorn app.main:app --reload --port $$PORT

test:
	pytest tests/

lint:
	flake8 .
