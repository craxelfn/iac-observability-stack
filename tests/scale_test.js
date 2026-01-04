import http from 'k6/http';
import { check, sleep } from 'k6';
import { Rate } from 'k6/metrics';

// Custom metrics
const errorRate = new Rate('errors');

// Test configuration
export const options = {
    stages: [
        // Warm up
        { duration: '2m', target: 50 },   // Ramp up to 50 users over 2 minutes

        // Stress test - trigger scaling
        { duration: '5m', target: 200 },  // Ramp to 200 users over 5 minutes
        { duration: '5m', target: 200 },  // Stay at 200 users for 5 minutes

        // Peak load - should trigger additional scaling
        { duration: '3m', target: 400 },  // Spike to 400 users
        { duration: '3m', target: 400 },  // Maintain peak for 3 minutes

        // Scale down
        { duration: '3m', target: 100 },  // Reduce to 100 users
        { duration: '3m', target: 0 },    // Ramp down to 0
    ],

    thresholds: {
        'http_req_duration': ['p(95)<2000'], // 95% of requests should be below 2s
        'http_req_failed': ['rate<0.1'],     // Error rate should be less than 10%
    },
};

// Replace ALB_DNS with your actual ALB DNS name
const ALB_DNS = __ENV.ALB_DNS || 'YOUR_ALB_DNS_HERE';
const BASE_URL = `http://${ALB_DNS}`;

export default function () {
    // Test multiple endpoints with different patterns
    const endpoints = [
        { url: `${BASE_URL}/health`, weight: 10 },
        { url: `${BASE_URL}/items?count=10`, weight: 50 },
        { url: `${BASE_URL}/items?count=50`, weight: 30 },
        { url: `${BASE_URL}/`, weight: 10 },
    ];

    // Select random endpoint based on weight
    const rand = Math.random() * 100;
    let cumulative = 0;
    let selectedEndpoint = endpoints[0].url;

    for (const endpoint of endpoints) {
        cumulative += endpoint.weight;
        if (rand < cumulative) {
            selectedEndpoint = endpoint.url;
            break;
        }
    }

    // Make request
    const response = http.get(selectedEndpoint);

    // Check response
    const success = check(response, {
        'status is 200': (r) => r.status === 200,
        'response time < 2s': (r) => r.timings.duration < 2000,
    });

    errorRate.add(!success);

    // Random think time between requests (0.5-2 seconds)
    sleep(Math.random() * 1.5 + 0.5);
}

export function handleSummary(data) {
    return {
        'tests/results/scale_test_summary.json': JSON.stringify(data),
        stdout: textSummary(data, { indent: ' ', enableColors: true }),
    };
}

function textSummary(data, options) {
    const indent = options.indent || '';
    const colors = options.enableColors;

    let summary = '\n' + indent + '=== LOAD TEST SUMMARY ===\n\n';

    summary += indent + `Total Requests: ${data.metrics.http_reqs.values.count}\n`;
    summary += indent + `Request Rate: ${data.metrics.http_reqs.values.rate.toFixed(2)} req/s\n`;
    summary += indent + `Failed Requests: ${data.metrics.http_req_failed.values.rate.toFixed(4) * 100}%\n\n`;

    summary += indent + 'Response Times:\n';
    summary += indent + `  Average: ${data.metrics.http_req_duration.values.avg.toFixed(2)} ms\n`;
    summary += indent + `  Median: ${data.metrics.http_req_duration.values.med.toFixed(2)} ms\n`;
    summary += indent + `  P95: ${data.metrics.http_req_duration.values['p(95)'].toFixed(2)} ms\n`;
    summary += indent + `  P99: ${data.metrics.http_req_duration.values['p(99)'].toFixed(2)} ms\n`;
    summary += indent + `  Max: ${data.metrics.http_req_duration.values.max.toFixed(2)} ms\n\n`;

    summary += indent + 'Virtual Users:\n';
    summary += indent + `  Max: ${data.metrics.vus_max.values.max}\n`;
    summary += indent + `  Duration: ${(data.state.testRunDurationMs / 1000 / 60).toFixed(2)} minutes\n\n`;

    return summary;
}
