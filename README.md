# Cloudflare Tunnel Manager

**Cloudflare Tunnel Manager** is a lightweight containerized solution designed to simplify the setup and management of Cloudflare Tunnels. It automates the creation of DNS records and updates tunnel configurations using the Cloudflare API. The container uses Python for intermediate actions and includes the `cloudflared` binary to handle tunneling.

## Features

- **DNS Automation**: Automatically creates DNS entries for hostnames defined in the `config.yml` file using the `cloudflared` CLI.
- **Configuration Management**: Updates tunnel configurations via the Cloudflare API.
- **Lightweight Design**: Built on a minimal Ubuntu base image with Python and the `cloudflared` binary.
- **Ease of Use**: Requires minimal setup with environment variables and configuration files.

### NOTE: 
This is provided as is. There is no guarantees, this could potentially break your tunnel. Use at your own risk. There is no official support.

## Table of Contents

- [Requirements](#requirements)
- [Setup](#setup)
- [Usage](#usage)
- [Environment Variables](#environment-variables)
- [Configuration](#configuration)

---

## Requirements

- **Cloudflare Account**: You need a Cloudflare account and an existing tunnel.
- **Cloudflare API Token**: The token must have the `Tunnel:Edit` permission for the specified account.
- **Docker**: Ensure Docker is installed and running on your system.

---

## Setup

### 1. Create a Cloudflare Tunnel
Follow these steps [here - via the dashboard](https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/get-started/create-remote-tunnel/)


### 2. Create a Cloudflare API Token

Follow these steps to create an API token with the required permissions:

1. Log in to the [Cloudflare Dashboard](https://dash.cloudflare.com/).
2. Navigate to **API Tokens** and click **Create Token**.
3. Use a **Custom Token** with:
   - **Permissions**: select *account* > *Cloudflare Tunnel* > *Edit*
   - **Account Resources**: Restrict to specific accounts or tunnels as needed.
4. Save the token for later use.

### 3. Create a `config` folder and put the following in

#### config.yml
Example talking to other containers:
```yml
tunnel: xxxxx
credentials-file: /root/.cloudflared/credentials.json

ingress:
  - hostname: scraper-hub-publish.example.com
    service: tcp://selenium-hub:4442
    originRequest:
      connectTimeout: 9999s
      httpHostHeader: scraper-hub-publish.example.com
      noTLSVerify: true
  - hostname: scraper-hub-subscribe.example.com
    service: tcp://selenium-hub:4443
    originRequest:
      connectTimeout: 9999s
      httpHostHeader:  scraper-hub-subscribe.example.com
      noTLSVerify: true
  - hostname: scraper-hub.example.com
    service: http://selenium-hub:4444
    originRequest:
      connectTimeout: 9999s
      httpHostHeader: scraper-hub.example.com
      noTLSVerify: true
  - hostname: www.example.com
    service: http://frontend:80
  - service: http_status:404

```
---

## Usage


```bash
docker run -d \
  --name cloudflare-tunnel-manager \
  -e TUNNEL_NAME="your-tunnel-name" \
  -e ACCOUNT_ID="your-cloudflare-account-id" \
  -e TUNNEL_ID="your-tunnel-id" \
  -e TUNNEL_TOKEN="your-tunnel-token" \
  -e CLOUDFLARE_API_TOKEN="your-cloudflare-api-token" \
  -e LOGGING_LEVEL="ERROR" \ # Optional, default is INFO
  -v ./cloudflared:/root/.cloudflared/ \
  jameswrc/cloudflare-tunnel-manager
```
or simply
```bash
docker compose up
```


## Environment Variables
| Variable               | Description                                                                                   | Default       | Required |
|------------------------|-----------------------------------------------------------------------------------------------|---------------|----------|
| `TUNNEL_NAME`          | The name of your Cloudflare Tunnel.                                                           | None          | Yes      |
| `ACCOUNT_ID`           | Your Cloudflare account ID.                                                                   | None          | Yes      |
| `TUNNEL_ID`            | The existing ID of the Cloudflare Tunnel.                                                     | None          | Yes      |
| `TUNNEL_TOKEN`         | The token for authenticating your Cloudflare Tunnel.                                          | None          | Yes      |
| `CLOUDFLARE_API_TOKEN` | The API token with `Tunnel:Edit` permission for managing DNS and tunnel configurations.       | None          | Yes      |
| `LOGGING_LEVEL`        | The logging verbosity level. Possible values: `DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`.| `INFO`        | No       |
| `CF_TUNNEL_OPTS`       | OPTIONAL - Sets the `tunnel run` cli opts. Can be overwritten at runtime                      | --config /root/.cloudflared/config.yml | No       |
| `CLOUDFLARED_CMD`       |  OPTIONAL - Sets the command to be run after the `create_dns_and_update_config.py` script is run. Can be overwritten at runtime | cloudflared tunnel ${CF_TUNNEL_OPTS} run | No       |
