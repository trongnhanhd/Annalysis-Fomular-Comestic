FROM python:3.12-slim
WORKDIR /app
ENV PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1
COPY requirements.txt requirements-mcp.txt ./
RUN pip install -r requirements-mcp.txt
COPY . .
RUN useradd -r -u 10001 rduser && chown -R rduser:rduser /app
USER rduser
EXPOSE 8000
CMD ["uvicorn","main:app","--host","0.0.0.0","--port","8000"]
