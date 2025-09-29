# API Documentation - ElevenLabs Voice Assistant

## Base URL
- Local: `http://localhost:8000`
- Docker: `http://localhost:8000`

## Authentication
- API Key required in environment variable: `ELEVENLABS_API_KEY`

---

## 🌐 HTTP Endpoints

### Health Check
```http
GET /health
```
**Response:**
```json
{
  "status": "healthy",
  "elevenlabs_configured": true,
  "active_conversations": 0
}
```

### List Available Agents
```http
GET /agents
```
**Response:**
```json
{
  "agents": [
    {
      "country_code": "AR",
      "agent_id": "agent_3601k52aw9jmej0a61svgk2hm0t1",
      "name": "Agente Porteño",
      "language": "es-AR"
    },
    // ... more agents
  ]
}
```

### Initialize Conversation
```http
POST /conversation/init
Content-Type: application/json
```
**Request Body:**
```json
{
  "caller_phone": "+54 11 1234-5678",
  "caller_name": "John Doe",  // optional
  "country_code": "AR",       // optional, default: "AR"
  "language": "es-AR",        // optional
  "custom_context": {}        // optional
}
```
**Response:**
```json
{
  "conversation_id": "550e8400-e29b-41d4-a716-446655440000",
  "agent_id": "agent_3601k52aw9jmej0a61svgk2hm0t1",
  "agent_name": "Agente Porteño",
  "websocket_url": "/ws/conversation/550e8400-e29b-41d4-a716-446655440000"
}
```

### Dial Number (Quick Call)
```http
POST /call/dial
Content-Type: application/json
```
**Request Body:**
```json
{
  "phone_number": "+54 11 1234-5678",
  "caller_info": {}  // optional
}
```
**Response:** Same as `/conversation/init`

### Get Conversation Status
```http
GET /conversation/{conversation_id}/status
```
**Response:**
```json
{
  "conversation_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "active",
  "agent_name": "Agente Porteño",
  "language": "es-AR"
}
```

### End Conversation
```http
DELETE /conversation/{conversation_id}
```
**Response:**
```json
{
  "message": "Conversation ended"
}
```

---

## 🔌 WebSocket Endpoints

### Simple WebSocket (for Dialer)
```
WS /ws
```
**Connection Flow:**
1. Connect to WebSocket
2. Send start_call message:
```json
{
  "type": "start_call",
  "from_number": "+54 11 1234-5678",
  "to_number": "ChevOz"
}
```
3. Receive call_started:
```json
{
  "type": "call_started",
  "conversation_id": "uuid",
  "agent_name": "Agente Porteño"
}
```
4. Exchange audio messages:
```json
// Send audio
{
  "type": "audio",
  "data": "base64_encoded_pcm16_audio"
}

// Receive audio
{
  "type": "audio",
  "data": "base64_encoded_pcm16_audio"
}
```
5. End call:
```json
{
  "type": "end_call"
}
```

### Conversation WebSocket
```
WS /ws/conversation/{conversation_id}
```
**Pre-requisite:** First call `/conversation/init` to get conversation_id

**Message Types:**
- `ready` - Sent by server when ready
- `audio` - Bidirectional audio data
- `user_transcript` - User's speech transcription
- `agent_response` - Agent's text response
- `error` - Error messages

---

## 🎭 Special Phone Numbers for Testing

| Number | Agent | Description |
|--------|-------|-------------|
| 111 | Agente Porteño | Buenos Aires accent |
| 222 | Agente Mexicano | Mexican Spanish |
| 333 | Agente Colombiana | Colombian Spanish |
| 444 | Agente Cordobés | Córdoba accent |
| 555 | Mendocino | Special Mendocino agent |

---

## 📡 Audio Format

- **Format:** PCM16
- **Sample Rate:** 16000 Hz
- **Channels:** Mono
- **Encoding:** Base64

---

## 🚀 Quick Start Examples

### cURL Examples

**1. Check Health:**
```bash
curl http://localhost:8000/health
```

**2. List Agents:**
```bash
curl http://localhost:8000/agents | jq
```

**3. Start a Call:**
```bash
curl -X POST http://localhost:8000/call/dial \
  -H "Content-Type: application/json" \
  -d '{"phone_number": "111"}' | jq
```

### JavaScript WebSocket Example
```javascript
// Connect to simple WebSocket
const ws = new WebSocket('ws://localhost:8000/ws');

ws.onopen = () => {
  // Start call
  ws.send(JSON.stringify({
    type: 'start_call',
    from_number: '111',
    to_number: 'ChevOz'
  }));
};

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('Received:', data.type);
  
  if (data.type === 'audio') {
    // Play audio (convert base64 to audio)
    playAudio(data.data);
  }
};

// Send audio
function sendAudio(base64Audio) {
  ws.send(JSON.stringify({
    type: 'audio',
    data: base64Audio
  }));
}
```

### Python Example
```python
import requests
import json

# Initialize conversation
response = requests.post('http://localhost:8000/conversation/init', 
    json={
        'caller_phone': '+54 11 1234-5678',
        'country_code': 'AR'
    }
)
data = response.json()
print(f"Conversation ID: {data['conversation_id']}")
print(f"WebSocket URL: ws://localhost:8000{data['websocket_url']}")
```

---

## 📊 Response Status Codes

| Code | Description |
|------|-------------|
| 200 | Success |
| 404 | Conversation not found |
| 500 | Internal server error |

---

## 🔍 Debugging

**View Logs:**
```bash
# Docker logs
docker-compose logs -f backend

# Local logs
python main.py
```

**Test WebSocket with wscat:**
```bash
npm install -g wscat
wscat -c ws://localhost:8000/ws
```