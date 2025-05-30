# Start with a lightweight Ubuntu image
FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive

# Install base dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3 \
    python3-pip \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python dependencies
COPY requirements.txt /app/
RUN pip3 install --no-cache-dir -r requirements.txt

# Set environment variables for cloudflared install
ARG TARGETARCH

# Download and install architecture-specific cloudflared binary
RUN case "$TARGETARCH" in \
      "amd64") ARCH="amd64" ;; \
      "arm64") ARCH="arm64" ;; \
      *) echo "Unsupported arch: $TARGETARCH" && exit 1 ;; \
    esac && \
    curl -L "https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-${ARCH}" \
      -o /usr/local/bin/cloudflared && \
    chmod +x /usr/local/bin/cloudflared

# Copy application code
COPY create_dns_and_update_config.py /app/
RUN chmod +x /app/create_dns_and_update_config.py

# Environment defaults
ENV CF_TUNNEL_OPTS="--config /root/.cloudflared/config.yml"
ENV CLOUDFLARED_CMD="cloudflared tunnel ${CF_TUNNEL_OPTS} run"

# Entrypoint
ENTRYPOINT ["/bin/sh", "-c", "python3 /app/create_dns_and_update_config.py && ${CLOUDFLARED_CMD}"]
