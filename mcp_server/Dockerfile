FROM python:3.12-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY server.py .

# Expose the internal port
EXPOSE 8000

# Run the server
# CMD ["python", "server.py"]
CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8000"]