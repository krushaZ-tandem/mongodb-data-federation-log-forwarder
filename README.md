# MongoDB Data Federation Log Forwarder

A Python-based log forwarding system that retrieves query logs from MongoDB Atlas Data Federation and forwards them to Azure Application Insights for monitoring and analytics.

## Features

- **Automated Log Retrieval**: Fetches Data Federation query logs from MongoDB Atlas using the Atlas Admin API v2
- **Azure Integration**: Forwards logs to Azure Application Insights for centralized monitoring
- **Configurable Throttling**: Built-in rate limiting to prevent overwhelming Azure services
- **Comprehensive Logging**: Detailed logging with custom dimensions for easy filtering and analysis
- **Secure Configuration**: Environment variable-based configuration with placeholder fallbacks

## Prerequisites

- Python 3.7+
- MongoDB Atlas account with Data Federation enabled
- Azure subscription with Application Insights resource
- MongoDB Atlas API key with appropriate permissions
- Azure Application Insights connection string

## Installation

1. Clone this repository:
```bash
git clone <repository-url>
cd MongoDB_LogForwardingDemo
```

2. Install required dependencies:
```bash
pip install requests opencensus-ext-azure
```

3. Create your configuration file:
```bash
cp config.py config.py.local
```

4. Edit `config.py` and update the configuration with your actual credentials:

```python
# MongoDB Atlas API Configuration
MONGODB_CONFIG = {
    "public_key": "your_mongodb_public_key",
    "private_key": "your_mongodb_private_key", 
    "group_id": "your_mongodb_group_id",
    "base_url": "https://cloud.mongodb.com/api/atlas/v2"
}

# Azure Application Insights Configuration
AZURE_CONFIG = {
    "connection_string": "your_application_insights_connection_string",
    "target_resource": "your_application_insights_resource_name"
}
```

## Configuration

## Configuration

### Environment Variables

The application uses environment variables for secure credential management. Set these variables before running the scripts:

#### Required Environment Variables

**MongoDB Atlas API Credentials:**
```bash
MONGODB_PUBLIC_KEY=your_mongodb_atlas_public_key
MONGODB_PRIVATE_KEY=your_mongodb_atlas_private_key  
MONGODB_GROUP_ID=your_mongodb_project_group_id
```

**Azure Application Insights Configuration:**
```bash
AZURE_APPINSIGHTS_CONNECTION_STRING=your_azure_application_insights_connection_string
AZURE_TARGET_RESOURCE=your_target_app_insights_resource_name
```

#### Setting Environment Variables

**Windows (PowerShell):**
```powershell
$env:MONGODB_PUBLIC_KEY="your_actual_public_key"
$env:MONGODB_PRIVATE_KEY="your_actual_private_key"
$env:MONGODB_GROUP_ID="your_actual_group_id"
$env:AZURE_APPINSIGHTS_CONNECTION_STRING="your_actual_connection_string"
$env:AZURE_TARGET_RESOURCE="your_actual_resource_name"
```

**Windows (Command Prompt):**
```cmd
set MONGODB_PUBLIC_KEY=your_actual_public_key
set MONGODB_PRIVATE_KEY=your_actual_private_key
set MONGODB_GROUP_ID=your_actual_group_id
set AZURE_APPINSIGHTS_CONNECTION_STRING=your_actual_connection_string
set AZURE_TARGET_RESOURCE=your_actual_resource_name
```

**Linux/macOS (Bash):**
```bash
export MONGODB_PUBLIC_KEY="your_actual_public_key"
export MONGODB_PRIVATE_KEY="your_actual_private_key"
export MONGODB_GROUP_ID="your_actual_group_id"
export AZURE_APPINSIGHTS_CONNECTION_STRING="your_actual_connection_string"
export AZURE_TARGET_RESOURCE="your_actual_resource_name"
```

#### Using .env file (Optional)

Create a `.env` file in the project root:
```bash
# .env file - DO NOT commit this file to version control
MONGODB_PUBLIC_KEY=your_actual_public_key
MONGODB_PRIVATE_KEY=your_actual_private_key
MONGODB_GROUP_ID=your_actual_group_id
AZURE_APPINSIGHTS_CONNECTION_STRING=your_actual_connection_string
AZURE_TARGET_RESOURCE=your_actual_resource_name
```

**Note**: If using a `.env` file, install `python-dotenv` and modify `config.py` to load it:
```bash
pip install python-dotenv
```

### Configuration Options

- **MONGODB_CONFIG**: MongoDB Atlas API credentials and settings
- **AZURE_CONFIG**: Azure Application Insights connection details
- **THROTTLING_CONFIG**: Rate limiting settings to prevent service overload
- **API_HEADERS**: MongoDB Atlas API v2 headers for proper API communication

## Usage

### Basic Usage (Original Script)

```bash
python download_query_logs.py
```

### Object-Oriented Version (Recommended)

```bash
python download_query_logs_refactored.py
```

The refactored version provides:
- Better error handling and logging
- Modular design with separate classes for different responsibilities
- Comprehensive documentation and type hints
- Improved maintainability

## Scripts

### `download_query_logs.py`
The original functional script that demonstrates the core log forwarding workflow.

### `download_query_logs_refactored.py`
An enhanced object-oriented version with:
- `FilteredAzureLogHandler`: Custom Azure log handler that filters unwanted metadata
- `AzureApplicationInsights`: Manages Azure Application Insights connections and testing
- `MongoDBAtlasAPI`: Handles all MongoDB Atlas API interactions
- `LogProcessor`: Processes and forwards logs with throttling
- `DataFederationLogForwarder`: Main orchestrator class

### `config.py`
Centralized configuration file with environment variable support and secure defaults.

## Monitoring

Once logs are forwarded to Azure Application Insights, you can query them using KQL:

```kql
// View all MongoDB Data Federation logs
traces 
| where customDimensions.source == "MongoDB Data Federation" 
| order by timestamp desc

// Filter by specific log types
traces 
| where customDimensions.log_type == "MongoDBDF"
| where customDimensions.severity == "I"
| order by timestamp desc

// View logs with specific attributes
traces 
| where customDimensions has "query"
| extend QueryDuration = tolong(customDimensions.attributes.durationMillis)
| where QueryDuration > 1000
| order by timestamp desc
```

## Security Considerations

- **Never commit real credentials**: The included `config.py` contains only placeholder values
- **Use environment variables**: For production deployments, use environment variables instead of hardcoded values
- **Rotate API keys regularly**: Follow security best practices for API key management
- **Monitor access logs**: Keep track of API usage and access patterns

## Troubleshooting

### Common Issues

1. **Configuration Import Error**: Ensure `config.py` exists and contains all required configuration sections
2. **MongoDB API Authentication**: Verify your API keys have the correct permissions for Data Federation access
3. **Azure Connection Issues**: Check your Application Insights connection string and resource accessibility
4. **Rate Limiting**: Adjust throttling configuration if you encounter rate limit errors

### Logging

The application provides comprehensive logging at different levels:
- **INFO**: General operation information and progress updates
- **WARNING**: Non-critical issues that don't stop execution
- **ERROR**: Critical errors that may affect functionality
- **DEBUG**: Detailed debugging information (enable with logging level changes)

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is provided as-is for educational and demonstration purposes. Please ensure you comply with MongoDB Atlas and Azure service terms when using this code.

## Support

For issues related to:
- **MongoDB Atlas API**: Consult the [MongoDB Atlas Documentation](https://docs.atlas.mongodb.com/api/)
- **Azure Application Insights**: Check the [Azure Application Insights Documentation](https://docs.microsoft.com/en-us/azure/azure-monitor/app/app-insights-overview)
- **This Code**: Open an issue in this repository
