export const options = {
  // Global options
  stages: [], // Will be set by scenario
  thresholds: {
    http_req_duration: ['p(95)<500'], // 95% of requests should be below 500ms
    http_req_failed: ['rate<0.01'],   // Less than 1% of requests should fail
  },
  // Scenario-specific options will be merged with these
};

// Scenario configurations
export const scenarios = {
  smoke_test: {
    stages: [
      { duration: '1m', target: 5 },
      { duration: '1m', target: 0 },
    ],
    thresholds: {
      http_req_duration: ['p(95)<300'], // Stricter threshold for smoke tests
    },
  },
  
  load_test: {
    stages: [
      { duration: '2m', target: 50 },   // Ramp up
      { duration: '5m', target: 50 },   // Stay at peak
      { duration: '2m', target: 0 },    // Ramp down
    ],
  },
  
  stress_test: {
    stages: [
      { duration: '2m', target: 100 },  // Ramp up
      { duration: '5m', target: 100 },  // Stay at peak
      { duration: '5m', target: 200 },  // Increase to breaking point
      { duration: '2m', target: 0 },    // Ramp down
    ],
  },
  
  spike_test: {
    stages: [
      { duration: '1m', target: 10 },   // Baseline
      { duration: '1m', target: 200 },  // Spike
      { duration: '1m', target: 10 },   // Recovery
      { duration: '1m', target: 0 },    // Scale down
    ],
  },
  
  soak_test: {
    stages: [
      { duration: '5m', target: 50 },   // Ramp up
      { duration: '4h', target: 50 },   // Stay at load
      { duration: '5m', target: 0 },    // Scale down
    ],
  },
};
