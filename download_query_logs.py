import requests
import gzip
import os
import logging
import json
import time
from opencensus.ext.azure.log_exporter import AzureLogHandler
from requests.auth import HTTPDigestAuth

# Import configuration
try:
    from config import MONGODB_CONFIG, AZURE_CONFIG, THROTTLING_CONFIG
except ImportError:
    print("Error: config.py file not found. Please create it using the template.")
    print("Copy config.py.template to config.py and fill in your credentials.")
    exit(1)

# Custom Azure Log Handler to filter out unwanted custom dimensions
class FilteredAzureLogHandler(AzureLogHandler):
    def emit(self, record):
        # Filter out unwanted fields from custom dimensions if they exist
        if hasattr(record, 'custom_dimensions') and record.custom_dimensions:
            filtered_dimensions = {}
            for key, value in record.custom_dimensions.items():
                # Only keep the fields we want
                if key not in ['fileName', 'module', 'lineNumber', 'process']:
                    filtered_dimensions[key] = value
            record.custom_dimensions = filtered_dimensions
        super().emit(record)

# Setup Azure Application Insights logger
logger = logging.getLogger("mongodb_atlas_logs")
logger.setLevel(logging.INFO)
azure_handler = FilteredAzureLogHandler(connection_string=AZURE_CONFIG["connection_string"])

# Configure the Azure handler to prevent queue overflow
azure_handler.setLevel(logging.INFO)
logger.addHandler(azure_handler)

# Console logger for debugging
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)

# Throttling configuration
BATCH_SIZE = THROTTLING_CONFIG["batch_size"]  # Process in smaller batches
BATCH_DELAY = THROTTLING_CONFIG["batch_delay"]  # Delay between batches (seconds)
LOG_DELAY = THROTTLING_CONFIG["log_delay"]  # Small delay between individual log entries (seconds)

def validate_azure_connection():
    """
    Validate Azure Application Insights connection
    """
    try:
        # Send a test log to verify connection
        test_logger = logging.getLogger("connection_test_df")
        test_handler = FilteredAzureLogHandler(connection_string=AZURE_CONFIG["connection_string"])
        test_logger.addHandler(test_handler)
        test_logger.setLevel(logging.INFO)
        
        logger.info("=== Azure Application Insights Configuration (Data Federation) ===")
        logger.info(f"Target Resource: {AZURE_CONFIG.get('target_resource', 'Not specified')}")
        logger.info("✓ Ready to send Data Federation logs to Application Insights")
        
        # Send a test log
        test_logger.info("Connection test from MongoDB Data Federation log forwarder", 
                        extra={"custom_dimensions": {
                            "test": True,
                            "source": "MongoDB Data Federation",
                            "log_type": "MongoDBDF",
                            "target_resource": AZURE_CONFIG.get('target_resource', 'Not specified')
                        }})
        
        logger.info("✓ Test log sent to Application Insights")
        return True
        
    except Exception as e:
        logger.error(f"✗ Failed to validate Azure Application Insights connection: {str(e)}")
        return False

def test_mongodb_api_basic_access(group_id, public_key, private_key):
    """
    Test basic MongoDB Atlas API access
    """
    url = f"https://cloud.mongodb.com/api/atlas/v2/groups/{group_id}"
    logger.info("Testing basic MongoDB Atlas API access...")
    
    try:
        resp = requests.get(url, auth=(public_key, private_key), timeout=30)
        
        if resp.status_code == 200:
            project_info = resp.json()
            logger.info(f"✓ MongoDB Atlas API access successful")
            logger.info(f"✓ Project Name: {project_info.get('name', 'Unknown')}")
            return True
        elif resp.status_code == 401:
            logger.error("✗ MongoDB Atlas API authentication failed (401 Unauthorized)")
            logger.error("  Check your public_key and private_key credentials")
            return False
        elif resp.status_code == 403:
            logger.error("✗ MongoDB Atlas API access forbidden (403 Forbidden)")
            logger.error("  Your API key may not have sufficient permissions")
            return False
        else:
            logger.error(f"✗ MongoDB Atlas API returned status code: {resp.status_code}")
            logger.error(f"  Response: {resp.text}")
            return False
            
    except Exception as e:
        logger.error(f"✗ Failed to connect to MongoDB Atlas API: {str(e)}")
        return False

def list_data_federation_instances(group_id, public_key, private_key):
    """
    List all Data Federation instances to see what's available using v2 API (to match Postman)
    """
    url = f"https://cloud.mongodb.com/api/atlas/v2/groups/{group_id}/dataFederation"
    headers = {
        'Accept': 'application/vnd.atlas.2025-03-12+json'
    }
    logger.info("Fetching available Data Federation instances using v2 API...")
    
    try:
        resp = requests.get(url, auth=(public_key, private_key), headers=headers, timeout=30)
        
        if resp.status_code == 200:
            # v2 API returns a results object
            data = resp.json()
            instances = data.get('results', [])
            
            if instances:
                logger.info(f"✓ Found {len(instances)} Data Federation instances:")
                for instance in instances:
                    name = instance.get('name', 'Unknown')
                    state = instance.get('state', 'Unknown')
                    logger.info(f"  - Name: {name}, State: {state}")
                return [instance.get('name') for instance in instances if instance.get('name')]
            else:
                logger.warning("✗ No Data Federation instances found in this project")
                return []
                
        elif resp.status_code == 401:
            logger.error("✗ Authentication failed when listing Data Federation instances")
            logger.error("  Check your API key permissions for Data Federation")
            return []
        elif resp.status_code == 403:
            logger.error("✗ Access forbidden when listing Data Federation instances")
            logger.error("  Your API key may not have Data Federation permissions")
            logger.error("  Required permission: Project Data Access Read/Write")
            return []
        else:
            logger.error(f"✗ Failed to list Data Federation instances: {resp.status_code}")
            logger.error(f"  Response: {resp.text}")
            return []
            
    except Exception as e:
        logger.error(f"✗ Exception when listing Data Federation instances: {str(e)}")
        return []

def download_data_federation_query_logs(group_id, data_federation_name, public_key, private_key, out_dir="mongodb_logs"):
    """
    Download Data Federation query logs for a given instance using Digest Authentication
    """
    url = f"https://cloud.mongodb.com/api/atlas/v2/groups/{group_id}/dataFederation/{data_federation_name}/queryLogs.gz"
    headers = {
        'Accept': 'application/vnd.atlas.2025-03-12+gzip'
    }
    logger.info(f"Downloading query logs from Data Federation: {data_federation_name}")
    try:
        os.makedirs(out_dir, exist_ok=True)
        out_path = os.path.join(out_dir, f"{data_federation_name}_queryLogs.gz")
        resp = requests.get(url, auth=HTTPDigestAuth(public_key, private_key), headers=headers, stream=True, timeout=600)
        if resp.status_code == 200:
            with open(out_path, "wb") as f:
                for chunk in resp.iter_content(chunk_size=8192):
                    f.write(chunk)
            logger.info(f"✓ Downloaded DF query logs to {out_path} ({os.path.getsize(out_path)} bytes)")
            return out_path
        elif resp.status_code == 404:
            logger.warning(f"No query logs found for {data_federation_name}.")
        else:
            logger.error(f"Failed to download DF logs: {resp.status_code} - {resp.text}")
    except Exception as e:
        logger.error(f"Exception downloading DF logs: {e}")
    return None

def process_mongodb_logs(gzip_file_path):
    """
    (No change) Process and forward logs to Application Insights, as in your code.
    """
    try:
        with gzip.open(gzip_file_path, 'rt', encoding='utf-8') as f:
            processed_count = 0
            error_count = 0
            batch_count = 0
            for idx, line in enumerate(f):
                line = line.strip()
                if not line:
                    continue
                try:
                    log_entry = json.loads(line)
                    
                    # Use the actual MongoDB message as the main log message
                    mongodb_message = log_entry.get("msg", "MongoDB Data Federation Log")
                    
                    custom_dimensions = {
                        "mongodb_timestamp": log_entry.get("t", {}).get("$date"),
                        "severity": log_entry.get("s"),
                        "component": log_entry.get("c"),
                        "context": log_entry.get("ctx"),
                        "attributes": log_entry.get("attr", {}),
                        "source": "MongoDB Data Federation",
                        "log_type": "MongoDBDF",
                        "target_resource": AZURE_CONFIG.get('target_resource', 'Not specified')
                    }
                    severity = log_entry.get("s", "I")
                    if severity in ["F", "E"]:
                        logger.error(mongodb_message, extra={"custom_dimensions": custom_dimensions})
                    elif severity == "W":
                        logger.warning(mongodb_message, extra={"custom_dimensions": custom_dimensions})
                    else:
                        logger.info(mongodb_message, extra={"custom_dimensions": custom_dimensions})
                    processed_count += 1
                    time.sleep(LOG_DELAY)
                    if processed_count % BATCH_SIZE == 0:
                        batch_count += 1
                        logger.info(f"Processed batch {batch_count} ({processed_count} total entries). Pausing to prevent queue overflow...")
                        time.sleep(BATCH_DELAY)
                except Exception as e:
                    error_count += 1
                    logger.error("Failed to parse MongoDBDF log line", extra={"custom_dimensions": {"error": str(e), "line": line[:500]}})
            logger.info(f"Log processing completed. Processed: {processed_count}, Errors: {error_count}")
            logger.info("Waiting for final telemetry to be sent...")
            time.sleep(5)
    except Exception as e:
        logger.error(f"Failed to process DF gzipped log file: {str(e)}")

def main_data_federation_log_forward(group_id, df_instance_name, public_key, private_key):
    # Validate Azure connection first
    if not validate_azure_connection():
        logger.error("Azure Application Insights validation failed. Please check your connection string.")
        return
    
    # Skip listing instances since we know FederatedDatabaseInstance0 exists from Postman
    logger.info("Skipping instance listing, proceeding directly to download as Postman works...")
    logger.info(f"Attempting to download logs for: {df_instance_name}")
    
    # Download DF query logs directly
    downloaded_logfile = download_data_federation_query_logs(group_id, df_instance_name, public_key, private_key)
    if downloaded_logfile:
        process_mongodb_logs(downloaded_logfile)
        logger.info("=== Data Federation Log Forwarding Summary ===")
        logger.info("All Data Federation logs have been forwarded to Azure Application Insights")
        logger.info(f"Target Resource: {AZURE_CONFIG.get('target_resource', 'Not specified')}")
        logger.info("Use this query in Application Insights:")
        logger.info('traces | where customDimensions.source == "MongoDB Data Federation" | order by timestamp desc')
    else:
        logger.error("No Data Federation logs downloaded.")
    
    logging.shutdown()  # Ensure all logs are flushed

# -- USAGE EXAMPLE --
if __name__ == "__main__":
    # Specify the DF instance name (from your API response, e.g., "FederatedDatabaseInstance0")
    df_instance_name = "FederatedDatabaseInstance0"
    main_data_federation_log_forward(
        group_id=MONGODB_CONFIG["group_id"],
        df_instance_name=df_instance_name,
        public_key=MONGODB_CONFIG["public_key"],
        private_key=MONGODB_CONFIG["private_key"]
    )