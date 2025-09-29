#!/bin/bash
# API Examples for ElevenLabs Voice Assistant
# Run this script to test all API endpoints

BASE_URL="http://localhost:8000"

echo "🧪 Testing ElevenLabs Voice Assistant API..."
echo "==========================================="

# 1. Health Check
echo -e "\n1️⃣ Health Check"
curl -s "$BASE_URL/health" | jq '.'

# 2. List Agents
echo -e "\n2️⃣ Available Agents"
curl -s "$BASE_URL/agents" | jq '.agents[] | {name, language, country_code}'

# 3. Initialize Conversation with Argentine Agent
echo -e "\n3️⃣ Initialize Conversation (Argentina)"
RESPONSE=$(curl -s -X POST "$BASE_URL/conversation/init" \
  -H "Content-Type: application/json" \
  -d '{
    "caller_phone": "+54 11 1234-5678",
    "caller_name": "Demo User",
    "country_code": "AR"
  }')
echo "$RESPONSE" | jq '.'
CONV_ID=$(echo "$RESPONSE" | jq -r '.conversation_id')

# 4. Check Conversation Status
echo -e "\n4️⃣ Conversation Status"
curl -s "$BASE_URL/conversation/$CONV_ID/status" | jq '.'

# 5. Quick Dial with Mexican Number
echo -e "\n5️⃣ Quick Dial (Mexico)"
curl -s -X POST "$BASE_URL/call/dial" \
  -H "Content-Type: application/json" \
  -d '{
    "phone_number": "222"
  }' | jq '.'

# 6. End Conversation
echo -e "\n6️⃣ End Conversation"
curl -s -X DELETE "$BASE_URL/conversation/$CONV_ID" | jq '.'

echo -e "\n✅ API tests completed!"
echo "=======================
