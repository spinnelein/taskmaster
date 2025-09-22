# TaskMaster API Postman Collection

This directory contains a comprehensive Postman collection for testing the TaskMaster API, including all endpoints, authentication methods, and advanced features.

## Files

- `TaskMaster-API.postman_collection.json` - Complete API collection with 40+ requests
- `TaskMaster-Environment.postman_environment.json` - Environment variables template
- `README.md` - This documentation file

## Quick Setup

### 1. Import Collection and Environment

1. Open Postman
2. Click **Import** button
3. Select both JSON files from this directory
4. Import both the collection and environment

### 2. Configure Environment Variables

1. Select the "TaskMaster API Environment" from the environment dropdown
2. Click the **eye icon** to edit environment variables
3. Set the required variables:

#### Required Variables

| Variable | Value | Description |
|----------|-------|-------------|
| `baseUrl` | `https://api.taskmaster.dev` | API base URL (or local dev URL) |
| `apiKey` | `tk_live_abc123...` | Your TaskMaster API key |

#### Optional Variables

| Variable | Value | Description |
|----------|-------|-------------|
| `sessionToken` | `sess_xyz789...` | Session token (if using session auth) |
| `userId` | `your-user-id` | Your user ID for testing |

### 3. Run the Collection

1. Start with the **🚀 Setup & Health Check** folder
2. Run folders in order for the complete testing experience
3. Or run individual requests as needed

## Collection Structure

The collection is organized into logical folders covering all API features:

### 🚀 Setup & Health Check
- **Health Check** - Verify API connectivity
- **Test Authentication** - Validate API key
- **Get Rate Limit Status** - Check current rate limits

### 📋 Tasks API v2
- **List All Tasks** - Pagination and sorting
- **Create New Task** - Task creation with validation
- **Get Task by ID** - Individual task retrieval
- **Update Task** - Partial updates
- **Filter Tasks** - Advanced filtering and sorting
- **Create Multiple Tasks (Batch)** - Batch operations
- **Search Tasks by Text** - Full-text search
- **Mark Task as Completed** - Status updates
- **Delete Test Task** - Cleanup

### 📅 Events API v2
- **List Events** - Event retrieval with pagination
- **Create Calendar Event** - Event creation
- **Get Calendar Events for Date Range** - Calendar view optimization
- **Update Event** - Event modifications
- **Delete Test Event** - Cleanup

### 🔍 Search API
- **Basic Search** - Full-text search across all entities
- **Search with Facets** - Faceted search results
- **Search Specific Entity Types** - Targeted search
- **Get Search Suggestions** - Auto-complete functionality
- **Analyze Search Query** - Query processing insights

### 📊 Export API
- **Export Tasks as CSV** - Data export with filtering
- **Export Events as JSON** - Multiple format support

### 🔗 WebSocket API
- **Get WebSocket Statistics** - Connection monitoring
- **Test WebSocket Task Creation Broadcast** - Real-time testing
- **Test All WebSocket Events** - Comprehensive event testing

### 📈 Analytics API
- **Get Usage Analytics (24h)** - Recent usage statistics
- **Get Detailed Analytics (7d)** - Weekly trends and breakdowns

### 🔔 Webhooks API
- **List Webhooks** - Webhook configuration
- **Create Webhook** - Event-driven integrations

### 🚨 Error Handling & Edge Cases
- **Test 401 Unauthorized** - Authentication error handling
- **Test 404 Not Found** - Resource not found scenarios
- **Test 422 Validation Error** - Input validation testing
- **Test Large Pagination Offset** - Edge case handling
- **Test Invalid Search Query** - Error response validation

### 🧹 Cleanup
- **Delete Batch Tasks** - Clean up test data
- **Delete Test Webhook** - Remove test webhook
- **Final Status Check** - Verify API health after testing

## Features Demonstrated

### Authentication
- ✅ API Key authentication (recommended)
- ✅ Session token authentication
- ✅ Error handling for invalid credentials

### Enhanced API v2 Features
- ✅ Pagination with metadata
- ✅ Advanced filtering (status, priority, date ranges)
- ✅ Multi-field sorting
- ✅ Field selection for payload optimization
- ✅ Full-text search
- ✅ Batch operations

### Real-time Features
- ✅ WebSocket connection testing
- ✅ Event broadcasting verification
- ✅ Real-time statistics monitoring

### Advanced Capabilities
- ✅ Search with faceting and suggestions
- ✅ Data export in multiple formats
- ✅ Webhook configuration and testing
- ✅ Usage analytics and monitoring

### Error Handling
- ✅ Comprehensive error response testing
- ✅ Edge case validation
- ✅ Rate limiting behavior
- ✅ Input validation testing

## Usage Patterns

### Running the Complete Test Suite

1. **Setup Phase**: Run "🚀 Setup & Health Check" folder
2. **Core Testing**: Run folders 2-8 in sequence
3. **Cleanup Phase**: Run "🧹 Cleanup" folder

### Individual Feature Testing

- **Tasks Management**: Run "📋 Tasks API v2" folder
- **Calendar Features**: Run "📅 Events API v2" folder
- **Search Testing**: Run "🔍 Search API" folder
- **Real-time Features**: Run "🔗 WebSocket API" folder

### Development Workflow

1. **Local Development**: Update `baseUrl` to `http://localhost:5000/api`
2. **Staging Testing**: Update `baseUrl` to staging environment
3. **Production Verification**: Use production URL with appropriate API key

## Environment Variables

### Auto-Populated Variables

These variables are automatically set during test execution:

| Variable | Purpose |
|----------|---------|
| `testTaskId` | ID of created test task |
| `testEventId` | ID of created test event |
| `webhookId` | ID of created test webhook |
| `batchTaskIds` | Array of batch-created task IDs |
| `rateLimitRemaining` | Current rate limit status |
| `timestamp` | Current timestamp for requests |
| Date ranges | Week/month boundaries for filtering |

### Manual Configuration

Update these based on your testing needs:

```javascript
// For local development
pm.environment.set('baseUrl', 'http://localhost:5000/api');

// For different environments
pm.environment.set('baseUrl', 'https://staging-api.taskmaster.dev');
pm.environment.set('baseUrl', 'https://api.taskmaster.dev');

// API key configuration
pm.environment.set('apiKey', 'tk_test_your_test_key_here');
pm.environment.set('apiKey', 'tk_live_your_production_key_here');
```

## Advanced Usage

### Custom Pre-request Scripts

The collection includes sophisticated pre-request scripts for:

- **Timestamp Generation**: Automatic timestamp creation
- **UUID Generation**: Helper function for generating UUIDs
- **Date Range Calculation**: Week/month boundaries for filtering
- **Dynamic Event Times**: Future datetime generation for events

### Test Automation

Each request includes comprehensive test scripts that:

- ✅ Validate response status codes
- ✅ Check response structure and data types
- ✅ Verify business logic correctness
- ✅ Extract and store data for subsequent requests
- ✅ Log useful information to console

### Error Validation

The collection thoroughly tests error scenarios:

- **Authentication Errors**: Invalid API keys, missing tokens
- **Validation Errors**: Missing required fields, invalid data
- **Not Found Errors**: Non-existent resource requests
- **Rate Limiting**: Simulated rate limit scenarios
- **Edge Cases**: Large offsets, empty queries, invalid parameters

## Environment Switching

### Development Environment

```json
{
  "baseUrl": "http://localhost:5000/api",
  "apiKey": "tk_test_development_key"
}
```

### Staging Environment

```json
{
  "baseUrl": "https://staging-api.taskmaster.dev",
  "apiKey": "tk_test_staging_key"
}
```

### Production Environment

```json
{
  "baseUrl": "https://api.taskmaster.dev", 
  "apiKey": "tk_live_production_key"
}
```

## Troubleshooting

### Common Issues

#### 1. Authentication Failures

**Problem**: 401 Unauthorized responses

**Solution**:
```javascript
// Verify API key format
console.log('API Key:', pm.environment.get('apiKey'));
// Should start with 'tk_test_' or 'tk_live_'

// Check environment selection
console.log('Environment:', pm.environment.name);
```

#### 2. Connection Errors

**Problem**: Cannot connect to API

**Solution**:
```javascript
// Check base URL
console.log('Base URL:', pm.environment.get('baseUrl'));

// Test basic connectivity
// Run "Health Check" request first
```

#### 3. Test Failures

**Problem**: Tests failing unexpectedly

**Solution**:
1. Check console output for detailed error messages
2. Verify environment variables are set correctly
3. Run "Setup & Health Check" folder first
4. Check API rate limits

#### 4. Rate Limiting

**Problem**: 429 Too Many Requests errors

**Solution**:
```javascript
// Check rate limit status
console.log('Rate Limit Remaining:', pm.environment.get('rateLimitRemaining'));

// Wait and retry if rate limited
// Rate limits reset hourly
```

### Debug Mode

Enable detailed logging by adding to request pre-scripts:

```javascript
// Enable debug logging
pm.environment.set('debug', 'true');

// Log all environment variables
Object.entries(pm.environment.toObject()).forEach(([key, value]) => {
    console.log(`${key}: ${value}`);
});
```

## Best Practices

### 1. Environment Management

- Use separate environments for dev/staging/production
- Keep API keys secure (use secret variable type)
- Don't commit API keys to version control

### 2. Test Organization

- Run setup requests before testing
- Use cleanup requests to remove test data
- Check rate limits before extensive testing

### 3. Error Handling

- Always check response status codes
- Validate response structure in tests
- Handle authentication errors gracefully

### 4. Data Management

- Use auto-populated variables for dynamic data
- Clean up test resources after use
- Avoid hardcoded IDs when possible

## Integration Examples

### Newman (Command Line)

Run the collection from command line:

```bash
# Install Newman
npm install -g newman

# Run entire collection
newman run TaskMaster-API.postman_collection.json \
  -e TaskMaster-Environment.postman_environment.json \
  --env-var "apiKey=tk_live_your_key_here"

# Run specific folder
newman run TaskMaster-API.postman_collection.json \
  -e TaskMaster-Environment.postman_environment.json \
  --folder "Tasks API v2" \
  --env-var "apiKey=tk_test_your_key_here"
```

### CI/CD Integration

```yaml
# GitHub Actions example
- name: Run API Tests
  run: |
    newman run postman/TaskMaster-API.postman_collection.json \
      -e postman/TaskMaster-Environment.postman_environment.json \
      --env-var "baseUrl=${{ secrets.API_BASE_URL }}" \
      --env-var "apiKey=${{ secrets.API_KEY }}" \
      --reporters cli,json \
      --reporter-json-export test-results.json
```

## Support

For issues with the Postman collection:

1. **Documentation**: Review this README and API documentation
2. **Test Output**: Check Postman console for detailed error messages
3. **API Status**: Check https://status.taskmaster.dev
4. **Support**: Contact api-support@taskmaster.dev

## Collection Updates

This collection is version 2.4.0 and matches the TaskMaster API v2.4.0 specification. When updating:

1. Check for new collection versions
2. Update environment variables as needed
3. Review changelog for breaking changes
4. Test critical workflows after updates

The collection will be updated alongside API releases to ensure compatibility and coverage of new features.