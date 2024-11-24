import http from 'k6/http';
import { check, sleep } from 'k6';
import { Rate } from 'k6/metrics';
import { randomString } from 'https://jslib.k6.io/k6-utils/1.2.0/index.js';

// Custom metrics
const errorRate = new Rate('errors');

// Test configuration
export const options = {
  scenarios: {
    // Smoke test
    smoke_test: {
      executor: 'constant-vus',
      vus: 1,
      duration: '1m',
      tags: { test_type: 'smoke' },
    },
    // Load test
    load_test: {
      executor: 'ramping-vus',
      startVUs: 0,
      stages: [
        { duration: '2m', target: 100 },  // Ramp up
        { duration: '5m', target: 100 },  // Stay at peak
        { duration: '2m', target: 0 },    // Ramp down
      ],
      tags: { test_type: 'load' },
    },
    // Stress test
    stress_test: {
      executor: 'ramping-vus',
      startVUs: 0,
      stages: [
        { duration: '2m', target: 100 },   // Normal load
        { duration: '5m', target: 200 },   // Stress point
        { duration: '2m', target: 300 },   // Breaking point
        { duration: '1m', target: 0 },     // Recovery
      ],
      tags: { test_type: 'stress' },
    },
    // Spike test
    spike_test: {
      executor: 'ramping-vus',
      startVUs: 0,
      stages: [
        { duration: '1m', target: 50 },    // Baseline
        { duration: '30s', target: 500 },  // Spike
        { duration: '1m', target: 50 },    // Recovery
      ],
      tags: { test_type: 'spike' },
    },
    // Soak test
    soak_test: {
      executor: 'ramping-vus',
      startVUs: 0,
      stages: [
        { duration: '2m', target: 50 },    // Ramp up
        { duration: '4h', target: 50 },    // Soak period
        { duration: '2m', target: 0 },     // Ramp down
      ],
      tags: { test_type: 'soak' },
    },
  },
  thresholds: {
    http_req_duration: ['p(95)<2000'], // 95% of requests should be below 2s
    http_req_failed: ['rate<0.01'],    // Less than 1% of requests should fail
    errors: ['rate<0.05'],             // Less than 5% error rate
  },
};

// Shared test data
const TEST_FILE_CONTENT = 'test content';
const BASE_URL = __ENV.BASE_URL || 'http://localhost:8000';

// Helper functions
function getAuthToken() {
  const maxRetries = 3;
  let retries = 0;
  
  while (retries < maxRetries) {
    try {
      const loginRes = http.post(`${BASE_URL}/api/v1/auth/login`, {
        username: 'test_user',
        password: 'test_password',
      });
      
      check(loginRes, {
        'login successful': (r) => r.status === 200,
      });
      
      if (loginRes.status === 200) {
        return loginRes.json('access_token');
      }
    } catch (e) {
      console.error(`Login attempt ${retries + 1} failed: ${e.message}`);
    }
    
    retries++;
    if (retries < maxRetries) {
      sleep(1);
    }
  }
  
  throw new Error('Failed to get auth token after multiple retries');
}

// Utility for retrying failed requests
function retryRequest(requestFn, maxRetries = 3) {
  let retries = 0;
  let lastError;
  
  while (retries < maxRetries) {
    try {
      const response = requestFn();
      if (response.status < 500) {  // Don't retry client errors
        return response;
      }
    } catch (e) {
      lastError = e;
      console.error(`Request attempt ${retries + 1} failed: ${e.message}`);
    }
    
    retries++;
    if (retries < maxRetries) {
      sleep(1);
    }
  }
  
  throw lastError || new Error('Request failed after multiple retries');
}

// Main test scenarios
export default function () {
  const token = getAuthToken();
  const headers = {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json',
  };

  // File upload test
  const fileName = `test-${randomString(8)}.txt`;
  const uploadRes = retryRequest(() => http.post(`${BASE_URL}/api/v1/storage/upload`, {
    file: http.file(TEST_FILE_CONTENT, fileName, 'text/plain'),
  }, {
    headers: { ...headers, 'Content-Type': 'multipart/form-data' },
  }));

  check(uploadRes, {
    'upload successful': (r) => r.status === 200,
  }) || errorRate.add(1);

  sleep(1);

  // AI processing test
  const processRes = retryRequest(() => http.post(`${BASE_URL}/api/v1/ai/process`, JSON.stringify({
    file_id: uploadRes.json('file_id'),
    operations: ['summarize', 'analyze'],
  }), { headers }));

  check(processRes, {
    'processing successful': (r) => r.status === 200,
  }) || errorRate.add(1);

  sleep(1);

  // Search test
  const searchRes = retryRequest(() => http.post(`${BASE_URL}/api/v1/search/semantic`, JSON.stringify({
    query: 'test document content',
  }), { headers }));

  check(searchRes, {
    'search successful': (r) => r.status === 200,
    'search has results': (r) => r.json('results').length > 0,
  }) || errorRate.add(1);

  sleep(1);

  // Batch processing test
  const batchRes = retryRequest(() => http.post(`${BASE_URL}/api/v1/ai/batch-process`, JSON.stringify({
    file_ids: [uploadRes.json('file_id')],
    operations: ['summarize'],
  }), { headers }));

  check(batchRes, {
    'batch processing successful': (r) => r.status === 200,
  }) || errorRate.add(1);

  sleep(1);
}

// Teardown function (cleanup after tests)
export function teardown() {
  const token = getAuthToken();
  const headers = {
    'Authorization': `Bearer ${token}`,
  };
  
  // Cleanup test data
  retryRequest(() => http.del(`${BASE_URL}/api/v1/test/cleanup`, null, { headers }));
}
