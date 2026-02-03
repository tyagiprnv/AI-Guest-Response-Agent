#!/bin/bash
# Test script for production features

set -e

API_URL="http://localhost:8000"
API_KEY="dev-key-12345"  # Update with your actual API key

echo "====================================="
echo "Production Features Test Suite"
echo "====================================="
echo ""

# Test 1: Authentication - Valid API Key
echo "Test 1: Valid API Key Authentication"
echo "-------------------------------------"
curl -X POST "${API_URL}/api/v1/generate-response" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: ${API_KEY}" \
  -d '{"message":"What time is check-in?","property_id":"prop_001"}' \
  -w "\nHTTP Status: %{http_code}\n" \
  -s | jq '.'
echo ""

# Test 2: Authentication - Invalid API Key (should fail with 401)
echo "Test 2: Invalid API Key (Expected: 401)"
echo "-------------------------------------"
curl -X POST "${API_URL}/api/v1/generate-response" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: invalid-key-xyz" \
  -d '{"message":"What time is check-in?","property_id":"prop_001"}' \
  -w "\nHTTP Status: %{http_code}\n" \
  -s | jq '.'
echo ""

# Test 3: Validation - Spam Pattern (should fail with 422)
echo "Test 3: Spam Pattern Validation (Expected: 422)"
echo "-------------------------------------"
curl -X POST "${API_URL}/api/v1/generate-response" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: ${API_KEY}" \
  -d '{"message":"aaaaaaaaaaaaaaaaaaa","property_id":"prop_001"}' \
  -w "\nHTTP Status: %{http_code}\n" \
  -s | jq '.'
echo ""

# Test 4: Validation - Invalid Property ID (should fail with 422)
echo "Test 4: Invalid Property ID Format (Expected: 422)"
echo "-------------------------------------"
curl -X POST "${API_URL}/api/v1/generate-response" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: ${API_KEY}" \
  -d '{"message":"What time is check-in?","property_id":"invalid-id"}' \
  -w "\nHTTP Status: %{http_code}\n" \
  -s | jq '.'
echo ""

# Test 5: Validation - Message Too Short (should fail with 422)
echo "Test 5: Message Too Short (Expected: 422)"
echo "-------------------------------------"
curl -X POST "${API_URL}/api/v1/generate-response" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: ${API_KEY}" \
  -d '{"message":"Hi","property_id":"prop_001"}' \
  -w "\nHTTP Status: %{http_code}\n" \
  -s | jq '.'
echo ""

# Test 6: Check Prometheus Metrics
echo "Test 6: Cost Tracking Metrics"
echo "-------------------------------------"
echo "Checking cost metrics in Prometheus..."
curl -s "${API_URL}/metrics" | grep agent_cost_usd_total
echo ""

# Test 7: Health Check (Public endpoint, no auth)
echo "Test 7: Public Health Endpoint (No Auth)"
echo "-------------------------------------"
curl -s "${API_URL}/health" | jq '.'
echo ""

echo "====================================="
echo "Test Suite Complete!"
echo "====================================="
