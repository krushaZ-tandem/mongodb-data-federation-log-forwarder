"""
Configuration file for MongoDB Atlas Data Federation Log Forwarder

Replace the placeholder values with your actual credentials and configuration.
For production use, consider using environment variables or a secure secrets management system.
"""

import os

# MongoDB Atlas Configuration
MONGODB_CONFIG = {
    "public_key": os.getenv("MONGODB_PUBLIC_KEY", "your_mongodb_public_key_here"),
    "private_key": os.getenv("MONGODB_PRIVATE_KEY", "your_mongodb_private_key_here"), 
    "group_id": os.getenv("MONGODB_GROUP_ID", "your_mongodb_project_id_here"),
    "base_url": "https://cloud.mongodb.com/api/atlas/v2"
}

# Azure Application Insights Configuration
AZURE_CONFIG = {
    "connection_string": os.getenv("AZURE_APPINSIGHTS_CONNECTION_STRING", "your_azure_application_insights_connection_string_here"),
    "target_resource": os.getenv("AZURE_TARGET_RESOURCE", "your_target_app_insights_resource_name_here")
}

# API Headers for MongoDB Atlas v2 API
API_HEADERS = {
    "Accept": "application/vnd.atlas.2025-03-12+json",
    "Accept-Gzip": "application/vnd.atlas.2025-03-12+gzip"
}

# Throttling Configuration
THROTTLING_CONFIG = {
    "batch_size": 50,  # Process logs in batches
    "batch_delay": 2.0,  # Delay between batches (seconds)
    "log_delay": 0.01,  # Delay between individual log entries (seconds)
    "telemetry_wait": 5.0  # Wait time for final telemetry to be sent (seconds)
}
