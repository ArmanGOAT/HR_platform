FROM python:3.12-slim
# Tesseract OCR will be added here when the OCR step is implemented:
#   RUN apt-get update && apt-get install -y --no-install-recommends tesseract-ocr && rm -rf /var/lib/apt/lists/*
WORKDIR /app
# shared preprocessing: the same code as in search and the offline branch
COPY packages/hr_core /packages/hr_core
RUN pip install --no-cache-dir /packages/hr_core
COPY services/ingest/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY services/ingest/worker.py .
CMD ["python", "-u", "worker.py"]
