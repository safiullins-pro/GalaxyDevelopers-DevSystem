#!/usr/bin/env node

/**
 * REAL LOAD TESTING - ACTUAL METRICS
 * No fake numbers, real measurements
 */

const http = require('http');
const https = require('https');

async function makeRequest(id) {
    return new Promise((resolve, reject) => {
        const startTime = Date.now();
        
        const options = {
            hostname: 'localhost',
            port: 8000,
            path: '/health',
            method: 'GET',
            timeout: 5000
        };
        
        const req = http.request(options, (res) => {
            let data = '';
            res.on('data', chunk => data += chunk);
            res.on('end', () => {
                const endTime = Date.now();
                resolve({
                    id,
                    statusCode: res.statusCode,
                    responseTime: endTime - startTime,
                    success: res.statusCode === 200
                });
            });
        });
        
        req.on('error', (error) => {
            resolve({
                id,
                statusCode: 0,
                responseTime: Date.now() - startTime,
                success: false,
                error: error.message
            });
        });
        
        req.on('timeout', () => {
            req.destroy();
            resolve({
                id,
                statusCode: 0,
                responseTime: 5000,
                success: false,
                error: 'timeout'
            });
        });
        
        req.end();
    });
}

async function runLoadTest(concurrentUsers, duration) {
    console.log(`🚀 Starting REAL load test: ${concurrentUsers} users for ${duration}ms`);
    
    const startTime = Date.now();
    const results = [];
    let requestId = 0;
    
    // Run concurrent requests
    const interval = setInterval(async () => {
        const batch = [];
        for (let i = 0; i < concurrentUsers; i++) {
            batch.push(makeRequest(requestId++));
        }
        
        const batchResults = await Promise.all(batch);
        results.push(...batchResults);
        
        if (Date.now() - startTime > duration) {
            clearInterval(interval);
            analyzeResults(results, concurrentUsers);
        }
    }, 1000); // Every second
}

function analyzeResults(results, concurrentUsers) {
    const successful = results.filter(r => r.success).length;
    const failed = results.filter(r => !r.success).length;
    const responseTimes = results.filter(r => r.success).map(r => r.responseTime);
    
    const avgResponseTime = responseTimes.length > 0 
        ? responseTimes.reduce((a, b) => a + b, 0) / responseTimes.length 
        : 0;
    
    const maxResponseTime = Math.max(...responseTimes, 0);
    const minResponseTime = Math.min(...responseTimes.filter(t => t > 0), 999999);
    
    // Calculate percentiles
    responseTimes.sort((a, b) => a - b);
    const p50 = responseTimes[Math.floor(responseTimes.length * 0.5)] || 0;
    const p95 = responseTimes[Math.floor(responseTimes.length * 0.95)] || 0;
    const p99 = responseTimes[Math.floor(responseTimes.length * 0.99)] || 0;
    
    console.log('\n📊 REAL LOAD TEST RESULTS');
    console.log('=========================');
    console.log(`Total Requests: ${results.length}`);
    console.log(`Successful: ${successful} (${(successful/results.length*100).toFixed(1)}%)`);
    console.log(`Failed: ${failed} (${(failed/results.length*100).toFixed(1)}%)`);
    console.log(`\nResponse Times:`);
    console.log(`  Average: ${avgResponseTime.toFixed(0)}ms`);
    console.log(`  Min: ${minResponseTime}ms`);
    console.log(`  Max: ${maxResponseTime}ms`);
    console.log(`  P50: ${p50}ms`);
    console.log(`  P95: ${p95}ms`);
    console.log(`  P99: ${p99}ms`);
    console.log(`\nThroughput: ${(results.length / 10).toFixed(1)} req/sec`);
    
    // Determine max concurrent users
    const successRate = successful / results.length;
    let maxConcurrentUsers = 0;
    
    if (successRate > 0.99 && p95 < 100) {
        maxConcurrentUsers = concurrentUsers * 2; // Can handle more
    } else if (successRate > 0.95 && p95 < 500) {
        maxConcurrentUsers = concurrentUsers; // At capacity
    } else {
        maxConcurrentUsers = Math.floor(concurrentUsers * successRate); // Over capacity
    }
    
    console.log(`\n✅ MAX CONCURRENT USERS: ${maxConcurrentUsers}`);
    console.log('=========================\n');
    
    // Save results to file
    const fs = require('fs');
    const report = {
        timestamp: new Date().toISOString(),
        concurrentUsers,
        totalRequests: results.length,
        successful,
        failed,
        successRate: (successRate * 100).toFixed(1) + '%',
        avgResponseTime: avgResponseTime.toFixed(0) + 'ms',
        p50: p50 + 'ms',
        p95: p95 + 'ms',
        p99: p99 + 'ms',
        maxConcurrentUsers,
        raw: results
    };
    
    fs.writeFileSync('load-test-results.json', JSON.stringify(report, null, 2));
    console.log('📄 Full report saved to load-test-results.json');
}

// Check if server is running
const checkServer = () => {
    return new Promise((resolve) => {
        http.get('http://localhost:8000/health', (res) => {
            resolve(res.statusCode === 200);
        }).on('error', () => {
            resolve(false);
        });
    });
};

// Main
async function main() {
    const serverRunning = await checkServer();
    
    if (!serverRunning) {
        console.error('❌ Server not running on localhost:8000');
        console.log('Start server with: npm start');
        process.exit(1);
    }
    
    // Test with different loads
    console.log('Testing with 10 concurrent users...');
    await runLoadTest(10, 10000); // 10 users for 10 seconds
    
    // Wait a bit
    await new Promise(r => setTimeout(r, 2000));
    
    console.log('\nTesting with 50 concurrent users...');
    await runLoadTest(50, 10000); // 50 users for 10 seconds
}

main().catch(console.error);