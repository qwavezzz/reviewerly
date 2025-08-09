FROM python:3.11-slim

WORKDIR /app

# Copy the monorepo into the container
COPY .. /app

RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# Expose the API port
EXPOSE 8000

CMD ["uvicorn", "gateway-api.main:app", "--host", "0.0.0.0", "--port", "8000"]