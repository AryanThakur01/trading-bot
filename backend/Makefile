.PHONY: run db-revision db-upgrade db-downgrade

run:
	@export $$(cat .env | xargs) && uvicorn app.main:app --reload --port $$PORT

db-revision:
	alembic revision --autogenerate -m "$(m)"

db-upgrade:
	alembic upgrade head

db-downgrade:
	alembic downgrade -1
