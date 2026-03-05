FROM python:3.12-slim

WORKDIR /app
COPY pyproject.toml README.md ./
COPY terminalbench ./terminalbench
COPY tasks ./tasks
COPY configs ./configs
COPY results ./results
RUN pip install --no-cache-dir .

EXPOSE 8741
CMD ["terminalbench", "serve", "--host", "0.0.0.0", "--port", "8741"]
