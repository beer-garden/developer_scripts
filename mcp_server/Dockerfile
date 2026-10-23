FROM python:3.12-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY server.py .

ENV MCP_BG_HOST=beer-garden \
    MCP_BG_PORT=2337 \
    MCP_BG_SSL=false \
    MCP_BG_CA_CERT= \
    MCP_BG_CLIENT_CERT= \
    MCP_BG_CLIENT_KEY= \
    MCP_BG_URL_PREFIX= \
    MCP_BIND_HOST=0.0.0.0 \
    MCP_BIND_PORT=8000 \
    MCP_BG_TAGS= 

# Expose the internal port
EXPOSE 8000

# Run the server
# CMD ["python", "server.py"]
CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8000"]