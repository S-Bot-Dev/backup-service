FROM postgres:16-bookworm

RUN apt-get update && apt-get install -y \
    python3 \
    python3-venv \
    python3-pip \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .

RUN python3 -m venv /venv \
    && /venv/bin/pip install --no-cache-dir -r requirements.txt

COPY app.py .

VOLUME ["/backups"]

ENV PATH="/venv/bin:$PATH"

CMD ["python3", "app.py"]
