# Curriculum Planning API

A FastAPI backend for generating curriculum plans using AI agents and Qdrant vector search.

## Features

- Generate curriculum plans based on curriculum, subject, grade, and number of terms
- Uses AI agents for content generation
- Vector search with Qdrant for relevant curriculum data
- RESTful API endpoints
- CORS enabled for frontend integration

## Setup

1. Clone the repository
2. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Set up environment variables in `.env` file
5. Run the server:
   ```bash
   uvicorn main:app --reload
   ```

## API Endpoints

- `POST /api/terms/plan` - Generate a curriculum plan
- `GET /api/projects` - Get available projects
- `GET /api/assessment-criteria` - Get assessment criteria
- `GET /health` - Health check endpoint

## Environment Variables

- `GROQ_API_KEY`: Your GROQ API key
- `OPENAI_API_KEY`: Your OpenAI API key
- `QDRANT_URL`: Qdrant server URL
- `QDRANT_API_KEY`: Qdrant API key
- `PORT`: Server port (default: 8000)
- `HOST`: Server host (default: 0.0.0.0)
- `DEBUG`: Enable debug mode (default: True)

## Development

To run the development server with auto-reload:

```bash
uvicorn main:app --reload
```

Access the API documentation at:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
