pybabel compile -d translations
uvicorn app.main:app --reload --host localhost --port 8000
