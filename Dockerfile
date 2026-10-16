FROM python:3.11-slim
ENV PYTHONUNBUFFERED=1 PORT=8080
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
# Bake the synthetic dataset into the image so the container is self-contained
RUN python -m shared.dataset
CMD exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT}
