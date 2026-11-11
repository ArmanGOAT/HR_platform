FROM python:3.12-slim
WORKDIR /app
# shared preprocessing: the same code as in ingest and the offline branch
COPY packages/hr_core /packages/hr_core
RUN pip install --no-cache-dir /packages/hr_core
COPY services/search/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY services/search/app ./app
EXPOSE 8001
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8001"]
