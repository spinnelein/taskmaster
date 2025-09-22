# TaskMaster API Code Examples

This directory contains comprehensive code examples for integrating with the TaskMaster API across multiple programming languages and frameworks.

## Directory Structure

```
examples/
├── README.md                    # This file
├── python/                      # Python examples and SDK
│   ├── sdk/                     # Official Python SDK
│   ├── examples/               # Usage examples
│   └── README.md               # Python-specific documentation
├── javascript/                 # JavaScript/Node.js examples
│   ├── sdk/                    # JavaScript SDK
│   ├── examples/              # Usage examples
│   └── README.md              # JavaScript-specific documentation
├── curl/                       # cURL examples
│   ├── basic-operations.sh     # Basic CRUD operations
│   ├── advanced-features.sh    # Advanced API features
│   └── README.md               # cURL documentation
├── postman/                    # Postman collections (see ../postman/)
└── integration-patterns/       # Common integration patterns
    ├── webhook-handlers/       # Webhook handling examples
    ├── real-time-sync/        # WebSocket integration
    └── batch-processing/      # Bulk operations
```

## Available Languages

### ✅ Python
- **SDK**: Full-featured Python SDK with async support
- **Examples**: Django, Flask, FastAPI integrations
- **Features**: Type hints, error handling, pagination helpers

### ✅ JavaScript/TypeScript
- **SDK**: Modern JavaScript SDK with TypeScript support
- **Examples**: Node.js, React, Vue.js, Express integrations
- **Features**: Promise-based, WebSocket support, auto-retry

### ✅ cURL
- **Scripts**: Complete bash scripts for all API operations
- **Examples**: Command-line automation, CI/CD integration
- **Features**: Error handling, environment configuration

### 🚧 Coming Soon
- **Go**: Go SDK and examples
- **PHP**: Laravel/Symfony integrations
- **C#**: .NET SDK and examples
- **Ruby**: Rails integration examples

## Quick Start by Language

### Python

```python
# Install SDK
pip install taskmaster-api

# Basic usage
from taskmaster import TaskMasterClient

client = TaskMasterClient(api_key="tk_live_abc123...")

# Create a task
task = client.tasks.create(
    title="Complete project documentation",
    priority="high",
    urgency=8,
    duration=120
)

# List tasks with filtering
tasks = client.tasks.list(
    status="active",
    priority=["high", "urgent"],
    limit=50
)
```

### JavaScript/Node.js

```javascript
// Install SDK
npm install @taskmaster/api

// Basic usage
const { TaskMasterClient } = require('@taskmaster/api');

const client = new TaskMasterClient({
    apiKey: 'tk_live_abc123...'
});

// Create a task
const task = await client.tasks.create({
    title: 'Complete project documentation',
    priority: 'high',
    urgency: 8,
    duration: 120
});

// List tasks with filtering
const tasks = await client.tasks.list({
    status: 'active',
    priority: ['high', 'urgent'],
    limit: 50
});
```

### cURL

```bash
# Set environment variables
export TASKMASTER_API_KEY="tk_live_abc123..."
export TASKMASTER_BASE_URL="https://api.taskmaster.dev"

# Create a task
curl -X POST "$TASKMASTER_BASE_URL/v2/tasks" \
  -H "X-API-Key: $TASKMASTER_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Complete project documentation",
    "priority": "high",
    "urgency": 8,
    "duration": 120
  }'

# List tasks
curl "$TASKMASTER_BASE_URL/v2/tasks?status=active&priority=high,urgent" \
  -H "X-API-Key: $TASKMASTER_API_KEY"
```

## Integration Patterns

### 1. Basic CRUD Operations
Examples of creating, reading, updating, and deleting resources across all languages.

### 2. Real-time Integration
WebSocket examples for live updates and collaborative features.

### 3. Webhook Handling
Server implementations for receiving and processing TaskMaster webhooks.

### 4. Batch Processing
Efficient handling of large datasets using batch operations and pagination.

### 5. Error Handling
Robust error handling patterns for production applications.

### 6. Authentication
Examples of different authentication methods and token management.

## Common Use Cases

### Task Management Dashboard
Complete examples of building task management interfaces:
- Task creation and updates
- Status filtering and sorting
- Real-time updates via WebSocket
- Bulk operations

### Calendar Integration
Calendar and scheduling examples:
- Event creation and management
- Calendar view optimization
- Recurring event handling
- Time pool management

### Project Management
Project and initiative management:
- Project lifecycle management
- Task dependencies and relationships
- Progress tracking and reporting
- Team collaboration features

### Analytics and Reporting
Data analysis and reporting examples:
- Usage analytics integration
- Custom report generation
- Data export and processing
- Performance monitoring

## Best Practices

### 1. Error Handling
- Always implement comprehensive error handling
- Use exponential backoff for retries
- Log errors appropriately for debugging

### 2. Rate Limiting
- Respect API rate limits
- Implement client-side rate limiting
- Use batch operations when possible

### 3. Authentication
- Store API keys securely
- Implement token refresh logic
- Use environment variables for configuration

### 4. Performance
- Use pagination for large datasets
- Implement caching where appropriate
- Minimize API calls with field selection

### 5. Real-time Features
- Implement proper WebSocket reconnection
- Handle connection failures gracefully
- Use appropriate event subscriptions

## Testing

Each language example includes:
- Unit tests for SDK functions
- Integration tests with the API
- Mock data for development
- Test utilities and helpers

### Running Tests

```bash
# Python
cd python && python -m pytest tests/

# JavaScript
cd javascript && npm test

# cURL
cd curl && ./run-tests.sh
```

## Contributing

To contribute new examples or improvements:

1. **Follow Conventions**: Match the established patterns for your language
2. **Include Tests**: Add appropriate test coverage
3. **Document**: Update README files and add inline comments
4. **Validate**: Test against the actual API
5. **Review**: Submit a pull request for review

### Example Contribution Template

```
examples/
├── [language]/
│   ├── sdk/
│   │   ├── client.js
│   │   ├── resources/
│   │   └── tests/
│   ├── examples/
│   │   ├── basic-usage.js
│   │   ├── advanced-features.js
│   │   └── integrations/
│   └── README.md
```

## Support

For questions about code examples:

1. **Check Documentation**: Review language-specific README files
2. **API Reference**: Consult the OpenAPI specification
3. **Community**: Ask questions in the developer forum
4. **Issues**: Report bugs or request examples via GitHub issues

## Version Compatibility

All examples are compatible with:
- **API Version**: 2.4.0+
- **Authentication**: API Key and Session Token methods
- **Features**: Enhanced v2 endpoints with pagination, filtering, and real-time capabilities

Examples are updated alongside API releases to ensure compatibility and demonstrate new features.