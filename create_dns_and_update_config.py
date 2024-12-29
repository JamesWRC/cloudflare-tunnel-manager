import yaml
import subprocess
import requests
import os
import sys
import logging


# REQUIRED Environment variables
TUNNEL_NAME = os.getenv("TUNNEL_NAME")
ACCOUNT_ID = os.getenv("ACCOUNT_ID")
TUNNEL_ID = os.getenv("TUNNEL_ID")
CLOUDFLARE_API_TOKEN = os.getenv("CLOUDFLARE_API_TOKEN")

# OPTIONAL Environment variables
LOGGING_LEVEL = os.getenv("LOGGING_LEVEL", "INFO").upper()  # Default to INFO level

# Configure logging
logging.basicConfig(
    level=LOGGING_LEVEL,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

logging.info("\t\t #### Cloudflare Tunnel Manager (CFTM) is starting... ####\t\t")

# Check if TUNNEL_TOKEN is provided. Needed for the cloudflare tunnel to run
if not os.getenv("TUNNEL_TOKEN"): 
    logging.error("Missing required environment variable TUNNEL_TOKEN. cloudflared needs this.")
    sys.exit(1)


# Constants
CONFIG_FILE = "/root/.cloudflared/config.yml"
CERT_FILE = "/root/.cloudflared/cert.pem"

# Function to parse config.yml
def parse_config(file_path: str) -> tuple:
    """
    Parse the config.yml file and return a tuple of warp_routing, hostnames, ingress rules.
    
    @param file_path: The path to the config.yml file.
    @return: A tuple of hostnames, ingress rules, and rules without hostnames.

    """
    with open(file_path, "r") as f:
        config = yaml.safe_load(f)

    # Get warp_routing value from config.yml
    warp_routing = config.get("warp_routing", False)

    hostnames = []
    for rule in config.get("ingress", []):
        if "hostname" in rule:
            if rule["hostname"] in hostnames:
                logging.error(f"Duplicate hostname found in config: {rule['hostname']}")
                sys.exit(1)

            hostnames.append(rule["hostname"])

    hostnames = [
        rule.get("hostname") for rule in config.get("ingress", []) if "hostname" in rule
    ]

    ingress_rules = config.get("ingress", [])

    return warp_routing, hostnames, ingress_rules

# Create DNS entry using cloudflared CLI
def create_dns_entry(hostname: str) -> None:
    """
    Create a DNS entry for the given hostname using the cloudflared CLI.

    @param hostname: The hostname for which to create the DNS entry.
    @return: None
    """
    try:
        logging.debug(f"Creating DNS entry for {hostname}")
        subprocess.run(
            ["cloudflared", "tunnel", "route", "dns", TUNNEL_NAME, hostname],
            check=True,
        )
        logging.debug(f"DNS entry created for {hostname}")
    except subprocess.CalledProcessError as e:
        logging.error(f"Failed to create DNS entry for {hostname}: {e}")
        sys.exit(1)

# Log changes in formatting
def log_changed_formatting(key:str, original:str, formatted:str) -> None:
    """
    Log changes in formatting for a given key-value pair.
    
    @param key: The key for the value being formatted.
    @param original: The original value before formatting.
    @param formatted: The formatted value after formatting.
    @return: None
    """
    logging.debug(f"Formatted '{key}' from: {original}|{type(original)} to: {formatted}|{type(formatted)}")

# Format configuration values
def format_ingres_config_for_API(config: dict) -> dict:
    """
    Format the configuration values to be used in the Cloudflare API to update the tunnel configuration.

    @param config: The configuration values to format.
    @return: The formatted configuration values.
    """
    logging.debug(f"Formatting configuration for API:\n\t{config}")

    formatted_config = {}
    for key, value in config.items():

        # Format 'originRequest' values
        if key == "originRequest":
            originRequest = value
            logging.debug(f"Formatting 'originRequest' values...")
            for origin_key, origin_value in originRequest.items():
    
                if origin_key == "connectTimeout":
                    # Remove non-numeric characters
                    cleaned_string = int(''.join(char for char in origin_value if char.isdigit()))
                    log_changed_formatting(origin_key, origin_value, cleaned_string)
                    # Update the value
                    originRequest[origin_key] = cleaned_string

        # Handle other key-value pairs here...

        # Update the key-value pair
        formatted_config[key] = value

    logging.debug(f"Formatted configuration for API:\n\t{formatted_config}")
    return formatted_config

# Function to update hostname configuration via Cloudflare API
def update_tunnels_config(warp_routing:bool, ingress_configs: list) -> None:
    """
    Make a PUT request to the Cloudflare API configurations to update the configuration for all hostnames found in the config.yml file.

    @param warp_routing: The warp_routing value to update.
    @param ingress_configs: The list of ingress configurations to update.
    @return: None
    """
    api_url = f"https://api.cloudflare.com/client/v4/accounts/{ACCOUNT_ID}/cfd_tunnel/{TUNNEL_ID}/configurations"
    
    headers = {
        "Authorization": f"Bearer {CLOUDFLARE_API_TOKEN}",
        "Content-Type": "application/json",
    }
    
    payload = {
        "config": {
            "ingress": ingress_configs,
            #... other configuration values
            "warp_routing": warp_routing
        },
    }

    response = requests.put(api_url, headers=headers, json=payload)
    if response.status_code == 200:
        logging.debug(f"Updated configuration for {hostname}: {response.json()}")
    else:
        logging.error(
            f"Failed to update configuration for {hostname}: {response.status_code}, provided payload:\n{payload}\nresponse text:\n{response.text}"
        )
        
        sys.exit(1)

# Function to login to Cloudflare Tunnel
def cf_tunnel_login() -> None:
    """
    Login to Cloudflare Tunnel using the cloudflared CLI.
    @return: None
    """
    if os.path.exists(CERT_FILE):
        logging.debug(f"{CERT_FILE} file exists. Assuming cert is valid and created by a previous successful login.")
    try:
        subprocess.run(
            ["cloudflared", "tunnel", "login"],
            check=True,
        )
        logging.debug("Successfully logged into Cloudflare Tunnel.")
    except subprocess.CalledProcessError as e:
        logging.error(f"Failed to login to Cloudflare Tunnel: {e}")
        sys.exit(1)

# Main script execution
if __name__ == "__main__":
    if not all([TUNNEL_NAME, ACCOUNT_ID, TUNNEL_ID, CLOUDFLARE_API_TOKEN]):
        logging.error("Missing required environment variables.")
        if not TUNNEL_NAME:
            logging.error("TUNNEL_NAME environment variable is missing.")
        if not ACCOUNT_ID:
            logging.error("ACCOUNT_ID environment variable is missing.")
        if not TUNNEL_ID:
            logging.error("TUNNEL_ID environment variable is missing.")
        if not CLOUDFLARE_API_TOKEN:
            logging.error("CLOUDFLARE_API_TOKEN environment variable is missing.")
        sys.exit(1)

    # Ensure config file exists
    if not os.path.exists(CONFIG_FILE):
        logging.error(f"Config file {CONFIG_FILE} not found.")
        sys.exit(1)

    # Login to Cloudflare Tunnel
    cf_tunnel_login()

    # Parse config.yml
    warp_routing, hostnames, ingress_rules = parse_config(CONFIG_FILE)

    # Process each hostname
    ingress_configs = []
    for hostname in list(hostnames):
        # Create DNS entry
        create_dns_entry(hostname)

        # Find the configuration for this hostname
        ingress_hostname_config = next(
            (rule for rule in ingress_rules if rule.get("hostname") == hostname), {}
        )

        # Add stuff for originRequest / warp-routing later if needed?

        # Format configuration values
        ingress_hostname_config = format_ingres_config_for_API(ingress_hostname_config)

        ingress_configs.append(ingress_hostname_config)

    # Merge ingress_configs so that rules without hostnames are included at the end
    rules_without_hostnames = [rule for rule in ingress_rules if "hostname" not in rule]
    ingress_configs += rules_without_hostnames # Append rules without hostnames to the end


    # Update Cloudflare API configuration for this hostname
    update_tunnels_config(warp_routing, ingress_configs)

    # Create 'ready.txt' file to indicate the script has completed
    with open("/root/ready.txt", "w") as f:
        f.write("Configuration updated successfully. Starting Cloudflare Tunnel.")

    logging.info("Configuration updated successfully. Starting Cloudflare Tunnel.")
