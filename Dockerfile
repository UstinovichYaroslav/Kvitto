FROM python:3.13

RUN pip install uv

WORKDIR /app

COPY pyproject.toml uv.lock ./

RUN uv pip install --system -e .

COPY . .

EXPOSE 8000

CMD ["sh", "-c", "cd src && alembic upgrade head && uvicorn main:app_main --host 0.0.0.0 --port 8000"]
