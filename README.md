# ElevenLabs Voice Assistant Demo 🎙️

Real-time voice assistant using ElevenLabs' conversational AI with WebSocket streaming.

## 🚀 Quick Start (30 seconds!)

### Option 1: Docker (Recommended)
```bash
# Clone and run
git clone https://github.com/yourusername/elevenlabs-voice-assistant
cd elevenlabs-voice-assistant

# Add your API key
echo "ELEVENLABS_API_KEY=your_key_here" > .env

# Run!
docker-compose up
```

### Option 2: Local Python
```bash
# Requirements: Python 3.8+
pip install -r requirements.txt

# Add your API key
export ELEVENLABS_API_KEY=your_key_here

# Run!
python main.py
```

**Visit:** http://localhost:8000 🎉

## 🎮 Demo Features

### 1. Web Dialer Interface
- Go to http://localhost:8000
- Enter a test number (111, 222, 333, 444, or 555)
- Click "Llamar" to start talking!

### 2. Multi-Language Agents
| Test Number | Agent | Language/Accent |
|------------|--------|-----------------|
| **111** | 🇦🇷 Porteño | Buenos Aires Spanish |
| **222** | 🇲🇽 Mexicano | Mexican Spanish |
| **333** | 🇨🇴 Colombiana | Colombian Spanish |
| **444** | 🇦🇷 Cordobés | Córdoba Spanish |
| **555** | 🍷 Mendocino | Special Agent |

### 3. Real-time Features
- ⚡ Low-latency voice streaming
- 🎯 Automatic language detection
- 💬 Live transcriptions
- 🔊 Bidirectional audio

## 📡 API Playground

### Test the API
```bash
# Check health
curl http://localhost:8000/health | jq

# List available agents
curl http://localhost:8000/agents | jq

# Start a conversation
curl -X POST http://localhost:8000/conversation/init \
  -H "Content-Type: application/json" \
  -d '{"caller_phone": "111"}' | jq
```

### WebSocket Testing
```javascript
// Browser console
const ws = new WebSocket('ws://localhost:8000/ws');
ws.onopen = () => console.log('Connected!');
ws.onmessage = (e) => console.log('Message:', JSON.parse(e.data));
```

## 🏗️ Architecture

```
┌─────────────┐     WebSocket      ┌──────────────┐
│   Browser   │◄──────────────────►│   FastAPI    │
│   Dialer    │     Audio/JSON     │   Backend    │
└─────────────┘                    └──────┬───────┘
                                          │
                                          │ HTTPS
                                          ▼
                                   ┌──────────────┐
                                   │  ElevenLabs  │
                                   │     API      │
                                   └──────────────┘
```

## 📁 Project Structure

```
hackaton_bugster/
├── main.py                     # FastAPI application entry point
├── api/                        # API layer
│   ├── routes/                # API routes
│   │   ├── health.py         # Health check endpoints
│   │   ├── agents.py         # Agent listing endpoints
│   │   ├── conversations.py  # Conversation management
│   │   └── static.py         # Static file serving
│   └── websockets/            # WebSocket handlers
│       └── handlers.py       # WebSocket endpoints
├── config/                     # Configuration module
│   └── settings.py            # Environment settings
├── domain/                     # Business domain layer
│   ├── models.py              # Domain models (Agent, CallSession)
│   └── services.py            # Business services
├── infrastructure/             # Infrastructure patterns
│   ├── agent_factory.py       # Factory pattern for agents
│   ├── conversational_ai.py   # ElevenLabs conversation wrapper
│   └── conversation_repository.py  # Storage pattern
├── services/                   # Service layer
│   ├── agent_mapping.py       # Agent configuration
│   ├── agent_service.py       # Agent service
│   ├── conversation_storage.py # Conversation persistence
│   └── elevenlabs_conversational.py # ElevenLabs client
├── frontend/                   # Frontend files
│   ├── dialer.html            # Main dialer interface
│   ├── call-screen.html       # Call screen interface
│   └── audio-converter.js     # Audio utilities
├── docker-compose.yml          # Docker configuration
├── Dockerfile                  # Docker image definition
├── requirements.txt            # Python dependencies
└── .env.example               # Environment variables example
```

## 📚 Documentation

- **[API Documentation](API_DOCUMENTATION.md)** - Full API reference
- **[FastAPI Docs](http://localhost:8000/docs)** - Interactive API docs
- **[ReDoc](http://localhost:8000/redoc)** - Alternative API docs

## 🧪 Testing Tips

1. **Voice Testing**
   - Speak clearly after connecting
   - Try different accents/speeds
   - Test interruptions

2. **API Testing**
   - Use the provided test numbers
   - Check WebSocket messages in browser DevTools
   - Monitor Docker logs: `docker-compose logs -f`

## 🛠️ Customization

### Add Your Own Agent
```python
# In infrastructure/agent_factory.py
"YOUR_CODE": {
    "agent_id": "your_elevenlabs_agent_id",
    "name": "Your Agent Name",
    "language": "en-US",
    "context": "Agent personality"
}
```

### Change Audio Settings
- Sample Rate: 16000 Hz (default)
- Format: PCM16
- See `frontend/call-screen.html` for browser audio handling

## 📊 Monitoring

```bash
# Watch logs
docker-compose logs -f

# Check active conversations
curl http://localhost:8000/health

# View agent status
curl http://localhost:8000/agents
```

## 🐛 Troubleshooting

| Issue | Solution |
|-------|----------|
| No audio | Check browser permissions |
| Connection failed | Verify API key in .env |
| Port in use | Change port in docker-compose.yml |
| Agent not responding | Check ElevenLabs dashboard |

## 🔗 Links

- [ElevenLabs Console](https://elevenlabs.io) - Manage agents
- [API Documentation](API_DOCUMENTATION.md) - Full API reference
- [FastAPI](https://fastapi.tiangolo.com/) - Framework docs

---

**Need an API Key?** Get one at [elevenlabs.io](https://elevenlabs.io) 🔑