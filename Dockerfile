FROM python:3.12-slim

RUN apt-get update && apt-get install -y \
    snmp \
    curl \
    bash \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the whole app folder into the container
COPY app/ .

# Update the path to discovery.sh
RUN chmod +x snmp.sh

CMD ["bash", "./snmp.sh"]
