FROM python:3.12-slim AS build
RUN apt-get update && apt-get install -y --no-install-recommends build-essential pkg-config default-libmysqlclient-dev && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY backend/requirements*.txt ./
RUN pip wheel --wheel-dir=/wheels -r requirements-production.txt
FROM python:3.12-slim
RUN apt-get update && apt-get install -y --no-install-recommends libmariadb3 && rm -rf /var/lib/apt/lists/* && useradd --uid 10001 --create-home app
WORKDIR /app
COPY --from=build /wheels /wheels
COPY backend/requirements*.txt ./
RUN pip install --no-index --find-links=/wheels -r requirements-production.txt && rm -rf /wheels
COPY --chown=app:app backend/ ./
RUN mkdir -p /app/staticfiles /app/media && chown -R app:app /app
USER app
EXPOSE 8000
CMD ["gunicorn","config.wsgi:application","--bind","0.0.0.0:8000","--workers","2","--timeout","60","--access-logfile","-"]
