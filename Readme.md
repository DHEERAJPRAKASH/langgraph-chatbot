# LangGraph Research Chatbot - Django Implementation

This Django application implements a research chatbot using LangGraph with multiple tools for searching research papers, Wikipedia, and current events.

## Features

- **Research Paper Search**: Query arXiv papers using paper IDs or search terms
- **Wikipedia Search**: Get information from Wikipedia articles
- **Current Events**: Search for recent news and trends using Tavily
- **Persistent Chat Sessions**: Store conversation history in the database
- **Real-time Chat Interface**: Modern web interface with typing indicators
- **Tool Integration**: Seamless integration of multiple AI tools

## Setup Instructions

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Environment Configuration

Create a `.env` file in your project root:

```env
# Django Settings
SECRET_KEY=your-secret-key-here
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# API Keys
GROQ_API_KEY=your-groq-api-key-here
TAVILY_API_KEY=your-tavily-api-key-here
```

### 3. Database Setup

```bash
python manage.py makemigrations
python manage.py migrate
python manage.py createsuperuser  # Optional: create admin user
```

### 4. Run the Application

```bash
python manage.py runserver
```

Visit `http://localhost:8000` to access the chatbot interface.

## API Endpoints

### Chat API
- **POST** `/api/chat/`
    - Send messages to the chatbot
    - Body: `{"message": "your message", "session_id": "optional"}`

### Chat History
- **GET** `/api/history/<session_id>/`
    - Get conversation history for a session

### Test Tools
- **POST** `/api/test/`
    - Test the chatbot tools functionality

## Usage Examples

### Research Paper Queries
```
"What is the research paper 1706.03762 about?"
"Find papers about attention mechanisms"
```

### Wikipedia Searches
```
"Tell me about quantum computing"
"What is machine learning?"
```

### Current Events
```
"What are the latest trends in AI?"
"Current news about climate change"
```

### Complex Queries
```
"What is the current weather in New York and then explain the paper 1706.03762?"
```

## Testing

### Test via Management Command
```bash
python manage.py test_chatbot --message "What is 1706.03762 about?"
```

### Test via API
```bash
curl -X POST http://localhost:8000/api/test/ \
  -H "Content-Type: application/json"
```

## Project Structure

```
project/
├── chatbot/
│   ├── management/
│   │   └── commands/
│   │       └── test_chatbot.py
│   ├── models.py          # Database models
│   ├── services.py        # LangGraph implementation
│   ├── views.py           # Django views
│   ├── urls.py            # URL routing
│   └── admin.py           # Django admin
├── templates/
│   └── chatbot/
│       └── index.html     # Chat interface
├── requirements.txt
├── .env
└── manage.py
```

## Key Components

### ChatbotService (services.py)
- Initializes LangGraph workflow
- Manages tool integration (Tavily, Wikipedia, arXiv)
- Processes messages through the graph

### Models (models.py)
- `ChatSession`: Stores chat sessions
- `ChatMessage`: Stores individual messages with type and content

### Views (views.py)
- `ChatbotView`: Renders the chat interface
- `ChatAPIView`: Handles API requests for chat
- `ChatHistoryView`: Retrieves conversation history

## Configuration

### API Keys Required
1. **GROQ_API_KEY**: For the Qwen language model
2. **TAVILY_API_KEY**: For web search functionality

### Environment Variables
All configuration is managed through environment variables loaded from `.env` file.

## Troubleshooting

### Common Issues

1. **Import Errors**: Ensure all dependencies are installed
2. **API Key Errors**: Verify API keys are correctly set in `.env`
3. **Database Errors**: Run migrations if tables don't exist
4. **Tool Errors**: Test individual tools using the test endpoint

### Debug Mode
Enable debug mode by setting `DEBUG=True` in `.env` for detailed error messages.

## Deployment Notes

- Set `DEBUG=False` in production
- Configure proper `ALLOWED_HOSTS`
- Use environment-specific settings for database
- Ensure API keys are securely managed
- Consider using Redis for session storage in production

## License

This project is open source and available under the MIT License.