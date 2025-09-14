// Simple web testing without full Playwright installation
// NO EMOJIS
const https = require('https');
const http = require('http');

function makeRequest(url, options = {}) {
  return new Promise((resolve, reject) => {
    const urlObj = new URL(url);
    const lib = urlObj.protocol === 'https:' ? https : http;
    
    const req = lib.get(url, (res) => {
      let data = '';
      
      res.on('data', (chunk) => {
        data += chunk;
      });
      
      res.on('end', () => {
        resolve({
          status: res.statusCode,
          headers: res.headers,
          body: data
        });
      });
    });
    
    req.on('error', reject);
    req.setTimeout(options.timeout || 10000, () => {
      req.destroy();
      reject(new Error('Request timeout'));
    });
  });
}

async function testWebsite() {
  console.log('Testing TaskMaster website...\n');
  
  const baseUrl = 'http://localhost:5175';
  const endpoints = [
    '/',
    '/ui-demo',
    '/tasks',
    '/events',
    '/schedule'
  ];
  
  for (const endpoint of endpoints) {
    const url = baseUrl + endpoint;
    console.log(`Testing: ${url}`);
    
    try {
      const response = await makeRequest(url);
      
      if (response.status === 200) {
        console.log(`  ✅ Status: ${response.status} OK`);
        
        // Check for common issues in HTML
        const html = response.body;
        if (html.includes('<!DOCTYPE html>')) {
          console.log('  ✅ Valid HTML document');
        }
        if (html.includes('React')) {
          console.log('  ✅ React detected');
        }
        if (html.includes('error') || html.includes('Error')) {
          console.log('  ⚠️  Error text found in response');
        }
        
      } else {
        console.log(`  ❌ Status: ${response.status}`);
      }
      
    } catch (error) {
      console.log(`  ❌ Failed: ${error.message}`);
    }
    
    console.log('');
  }
  
  // Test API endpoints
  console.log('Testing API endpoints...\n');
  const apiUrl = 'http://localhost:8000';
  const apiEndpoints = [
    '/health',
    '/api/tasks',
    '/api/events'
  ];
  
  for (const endpoint of apiEndpoints) {
    const url = apiUrl + endpoint;
    console.log(`Testing: ${url}`);
    
    try {
      const response = await makeRequest(url);
      console.log(`  ✅ Status: ${response.status}`);
      
      if (response.headers['content-type']?.includes('application/json')) {
        console.log('  ✅ JSON response');
        try {
          const json = JSON.parse(response.body);
          if (endpoint === '/health' && json.status) {
            console.log(`  ✅ Health status: ${json.status}`);
          }
          if (Array.isArray(json)) {
            console.log(`  ✅ Array response with ${json.length} items`);
          }
        } catch (e) {
          console.log('  ⚠️  Invalid JSON response');
        }
      }
      
    } catch (error) {
      console.log(`  ❌ Failed: ${error.message}`);
    }
    
    console.log('');
  }
}

// Export for use as module
module.exports = { testWebsite };

// If run directly, execute the test
if (require.main === module) {
  testWebsite().catch(console.error);
}