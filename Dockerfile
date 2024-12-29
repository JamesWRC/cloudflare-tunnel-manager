# Start with a lightweight Ubuntu image
FROM ubuntu:22.04

# Set non-interactive mode for apt-get
ENV DEBIAN_FRONTEND=noninteractive

# Install necessary packages
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3 \
    python3-pip \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Set the working directory
WORKDIR /app

# Install Python dependencies
COPY requirements.txt /app/
RUN pip3 install --no-cache-dir -r requirements.txt

# Download and install the cloudflared binary
RUN curl -L https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64 \
    -o /usr/local/bin/cloudflared && \
    chmod +x /usr/local/bin/cloudflared

# Copy the Python script
COPY create_dns_and_update_config.py /app/

# Ensure the Python script is executable
RUN chmod +x /app/create_dns_and_update_config.py

# Set default environment variables for the cloudflared tunnel
ENV CF_TUNNEL_OPTS="--config /root/.cloudflared/config.yml"
ENV CLOUDFLARED_CMD="cloudflared tunnel ${CF_TUNNEL_OPTS} run"


# Set the entrypoint to the Python script. Docs for cloudflared https://fig.io/manual/cloudflared
ENTRYPOINT ["/bin/sh", "-c", "python3 /app/create_dns_and_update_config.py && ${CLOUDFLARED_CMD}"]

