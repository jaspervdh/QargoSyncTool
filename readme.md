# Assignment for the role of Junior Integration Engineer (Jasper Van den Hemel)
Python tool for synchronizing resource unavailabilities between a local Qargo environment and a master data system, ensuring planners have up-to-date information about resource availability.

## Overview

This tool connects to two Qargo environments via their REST API:
- **Master Data Environment**: The source of truth for unavailability data
- **Local Environment**: The destination where unavailabilities are synchronized

The tool matches resources between environments and performs create, update, and delete operations to keep unavailability data in sync.

## Requirements

- Python 3.8 or higher
- Internet connection
- Valid API credentials for both Qargo environments

## Installation

1. **Clone or download this repository**

2. **Install dependencies:**
creating conda env with needed dependencies:
```bash
conda create --name <env> --file requirements.txt
```

3. **Create a `.env` file** in the project root with your credentials:
```env
CLIENT_ID=your-local-client-id@client.qargo-api.com
CLIENT_SECRET=your-local-client-secret

MASTER_DATA_CLIENT_ID=your-master-client-id@client.qargo-api.com
MASTER_DATA_CLIENT_SECRET=your-master-client-secret
```

## Usage

### Basic Execution

Run the synchronization once:

```bash
python main.py
```

This will:
1. Authenticate with both environments
2. Match resources between environments
3. Sync unavailabilities for matched resources (2025 only)
4. Display statistics about created/updated/deleted records

### Expected Output

```
2025-11-04 10:30:15 [INFO] Authenticating with Qargo API...
2025-11-04 10:30:16 [INFO] Retrieved .. resources from API
2025-11-04 10:30:16 [INFO] Matched .. out of .. resources
2025-11-04 10:30:18 [INFO] Sync complete: {'created': .., 'updated': .., 'deleted': .., 'unchanged': .., 'errors': ..}
```

## Design Patterns

This project implements several software design patterns to ensure maintainability and extensibility:

### 1. Repository Pattern
**Location**: [`unavailability_repository.py`](/unavailability_repository.py)

The Repository Pattern abstracts data access logic, providing a clean interface for CRUD operations without exposing implementation details.
Ensuring easy swap of data sources without neededing changes in the business logic.

```python
class UnavailabilityRepository:
    def get_all_for_resource(self, resource_id: UUID)
    def create(self, unavailability: Unavailability)
    def update(self, unavailability: Unavailability)
    def delete(self, resource_id: UUID, unavailability_id: UUID)
```

### 2. Strategy Pattern
**Location**: [`resource_matcher.py`](resource_matcher.py)

The Strategy Pattern enables flexible resource matching by defining a family of algorithms (matching strategies) that can be selected at runtime.
This makes it easy to add new (external) matching strategies and change their priority.
```python
class ResourceMatcher:
    def __init__(self, master_resources):
        self.match_strategies = [
            self._match_by_custom_fields,
            self._match_by_license_plate,
            self._match_by_name
        ]
```

### 3. Context Manager Pattern
**Location**: [`qargo_client.py`](qargo_client.py)

The Context Manager Pattern ensures proper resource cleanup (HTTP sessions) using Python's `with` statement.
This prevents connection leaks.

```python
with QargoClient(token) as client:
    # Client is automatically closed after this block
    resources = client.get_resources()
```

### 4. Facade Pattern
**Location**: [`qargo_client.py`](qargo_client.py)

The QargoClient class provides a simplified interface to the Qargo API, hiding implementation details like pagination and authentication headers.

```python
# Complex pagination logic hidden behind simple method
resources = client.get_resources()
```

## Project Structure

```
.
├── main.py                          # Entry point and orchestration
├── qargo_auth.py                    # Authentication with token caching
├── qargo_client.py                  # API client with pagination
├── resource_matcher.py              # Resource matching strategies
├── unavailability_repository.py     # Data access layer
├── classes/
|   └── unavailability.py           # Pydantic data model
```

## Security Considerations

- Credentials stored in environment variables (never hardcoded)
- Token caching reduces authentication requests
- HTTPS-only API communication
- No sensitive data in logs

## Error Handling

The tool implements comprehensive error handling:

- **API failures**: Logged with details, sync continues for other resources
- **Authentication errors**: Clear error messages with troubleshooting hints
- **Missing credentials**: Validation on startup
- **Network issues**: Proper exception handling and logging
- **Partial failures**: Statistics track errors per resource
