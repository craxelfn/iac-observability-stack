/**
 * MasterProject Load Test Script
 * 
 * This k6 script tests the API endpoints with two scenarios:
 * 1. Steady State: 10 VUs for 5 minutes
 * 2. Spike Test: Ramp from 1 to 50 VUs
 * 
 * Usage:
 *   k6 run tests/load_test.js
 *   k6 run tests/load_test.js --env ALB_DNS=your-alb-dns.amazonaws.com
 */

import http from 'k6/http';
import { check, sleep } from 'k6';
import { Rate, Trend, Counter } from 'k6/metrics';

// Custom metrics
const errorRate = new Rate('errors');
const healthDuration = new Trend('health_duration');
const itemsDuration = new Trend('items_duration');
const errorDuration = new Trend('error_duration');
const requestCounter = new Counter('total_requests');

// Test configuration
const BASE_URL = __ENV.ALB_DNS 
  ? `http://${__ENV.ALB_DNS}` 
  : 'http://localhost:8080';

// Thresholds for pass/fail criteria
export const options = {
  scenarios: {
    // Scenario 1: Steady state load
    steady_state: {
      executor: 'constant-vus',
      vus: 10,
      duration: '5m',
      startTime: '0s',
      tags: { scenario: 'steady_state' },
    },
    // Scenario 2: Spike test (uncomment to run)
    // spike_test: {
    //   executor: 'ramping-vus',
    //   startVUs: 1,
    //   stages: [
    //     { duration: '2m', target: 50 },  // Ramp up to 50 VUs
    //     { duration: '3m', target: 50 },  // Hold at 50 VUs
    //     { duration: '1m', target: 0 },   // Ramp down
    //   ],
    //   startTime: '6m',  // Start after steady state
    //   tags: { scenario: 'spike_test' },
    // },
  },
  thresholds: {
    // p95 latency should be under 500ms
    'http_req_duration{scenario:steady_state}': ['p(95)<500'],
    // Error rate should be under 1%
    'errors': ['rate<0.01'],
    // Individual endpoint thresholds
    'health_duration': ['p(95)<100'],
    'items_duration': ['p(95)<500'],
  },
};

// Request distribution weights
const WEIGHTS = {
  items: 70,   // 70% of requests
  health: 20,  // 20% of requests
  error: 10,   // 10% of requests
};

/**
 * Select endpoint based on weighted distribution
 */
function selectEndpoint() {
  const rand = Math.random() * 100;
  if (rand < WEIGHTS.items) {
    return 'items';
  } else if (rand < WEIGHTS.items + WEIGHTS.health) {
    return 'health';
  }
  return 'error';
}

/**
 * Test the /health endpoint
 */
function testHealth() {
  const start = Date.now();
  const response = http.get(`${BASE_URL}/health`, {
    tags: { endpoint: 'health' },
  });
  healthDuration.add(Date.now() - start);
  requestCounter.add(1);

  const success = check(response, {
    'health: status is 200': (r) => r.status === 200,
    'health: has status field': (r) => {
      try {
        return JSON.parse(r.body).status === 'healthy';
      } catch {
        return false;
      }
    },
    'health: has timestamp': (r) => {
      try {
        return JSON.parse(r.body).timestamp !== undefined;
      } catch {
        return false;
      }
    },
  });

  errorRate.add(!success);
  return response;
}

/**
 * Test the /items endpoint
 */
function testItems() {
  const count = Math.floor(Math.random() * 20) + 1; // 1-20 items
  const start = Date.now();
  const response = http.get(`${BASE_URL}/items?count=${count}`, {
    tags: { endpoint: 'items' },
  });
  itemsDuration.add(Date.now() - start);
  requestCounter.add(1);

  const success = check(response, {
    'items: status is 200': (r) => r.status === 200,
    'items: returns array': (r) => {
      try {
        const body = JSON.parse(r.body);
        return Array.isArray(body.items);
      } catch {
        return false;
      }
    },
    'items: correct count': (r) => {
      try {
        const body = JSON.parse(r.body);
        return body.count === count;
      } catch {
        return false;
      }
    },
  });

  errorRate.add(!success);
  return response;
}

/**
 * Test the /error endpoint
 */
function testError() {
  const start = Date.now();
  const response = http.get(`${BASE_URL}/error`, {
    tags: { endpoint: 'error' },
  });
  errorDuration.add(Date.now() - start);
  requestCounter.add(1);

  // This endpoint intentionally returns 500, so we expect 500
  const success = check(response, {
    'error: status is 500': (r) => r.status === 500,
    'error: has error message': (r) => {
      try {
        return JSON.parse(r.body).error !== undefined;
      } catch {
        return false;
      }
    },
  });

  // Don't count intentional errors as failures
  // errorRate.add(!success);
  return response;
}

/**
 * Setup function - runs once before test
 */
export function setup() {
  console.log(`Testing API at: ${BASE_URL}`);
  
  // Verify API is accessible
  const healthCheck = http.get(`${BASE_URL}/health`);
  if (healthCheck.status !== 200) {
    console.error(`API health check failed with status: ${healthCheck.status}`);
    console.error(`Response: ${healthCheck.body}`);
  } else {
    console.log('API health check passed');
  }

  return { startTime: new Date().toISOString() };
}

/**
 * Main test function - runs for each VU iteration
 */
export default function () {
  const endpoint = selectEndpoint();
  
  switch (endpoint) {
    case 'health':
      testHealth();
      break;
    case 'items':
      testItems();
      break;
    case 'error':
      testError();
      break;
  }

  // Random sleep between 100ms and 1s to simulate real user behavior
  sleep(Math.random() * 0.9 + 0.1);
}

/**
 * Teardown function - runs once after test
 */
export function teardown(data) {
  console.log(`Test started at: ${data.startTime}`);
  console.log(`Test completed at: ${new Date().toISOString()}`);
}

/**
 * Handle summary generation
 */
export function handleSummary(data) {
  const summary = {
    'stdout': textSummary(data, { indent: '  ', enableColors: true }),
  };
  
  // Also output JSON summary
  summary['tests/results/summary.json'] = JSON.stringify(data, null, 2);
  
  return summary;
}

/**
 * Simple text summary formatter
 */
function textSummary(data, options) {
  const lines = [
    '\n',
    '='.repeat(60),
    'MasterProject Load Test Results',
    '='.repeat(60),
    '',
    `Total Requests: ${data.metrics.total_requests ? data.metrics.total_requests.values.count : 'N/A'}`,
    `Duration: ${Math.round(data.state.testRunDurationMs / 1000)}s`,
    '',
    'Response Times:',
    `  Health Endpoint p95: ${data.metrics.health_duration ? Math.round(data.metrics.health_duration.values['p(95)']) : 'N/A'}ms`,
    `  Items Endpoint p95: ${data.metrics.items_duration ? Math.round(data.metrics.items_duration.values['p(95)']) : 'N/A'}ms`,
    '',
    `Error Rate: ${data.metrics.errors ? (data.metrics.errors.values.rate * 100).toFixed(2) : '0'}%`,
    '',
    '='.repeat(60),
    '',
  ];
  
  return lines.join('\n');
}
