# Environment Setup Guide

## Environment Variables

Create a `.env` file in the project root with the following variables:

```env
# Application Configuration
APP_NAME="Azure Cloud Grooming Service"
APP_VERSION="0.1.0"
DEBUG=false

# Database Configuration
# For local development (SQLite)
DATABASE_URL="sqlite:///./grooming_service.db"

# For Azure SQL Database (example)
# DATABASE_URL="mssql+pyodbc://username:password@server.database.windows.net/grooming_db?driver=ODBC+Driver+18+for+SQL+Server"

# For PostgreSQL (example)
# DATABASE_URL="postgresql://username:password@localhost:5432/grooming_db"

# API Configuration
API_V1_PREFIX="/api/v1"
```

## Quick Setup

1. Copy the example above to a new `.env` file:
   ```bash
   # On Windows PowerShell
   @"
   APP_NAME="Azure Cloud Grooming Service"
   APP_VERSION="0.1.0"
   DEBUG=false
   DATABASE_URL="sqlite:///./grooming_service.db"
   API_V1_PREFIX="/api/v1"
   "@ | Out-File -FilePath .env -Encoding utf8
   ```

2. Or create it manually:
   - Create a new file named `.env` in the project root
   - Copy the configuration above
   - Adjust values as needed

## Notes

- The `.env` file is already in `.gitignore` and will not be committed
- For production, use secure database credentials
- SQLite is recommended for local development only
