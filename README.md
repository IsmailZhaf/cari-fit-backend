## Vornexus Backend

### Environment Variables

The following environment variables should be set in your `.env` file:

```
# Mistral API
MISTRAL_API_KEY=your_mistral_api_key

# OpenAI API for embeddings
OPENAI_API_KEY=your_openai_api_key
```

### ChromaDB Setup

This application uses ChromaDB for vector storage. To run ChromaDB:

```bash
chroma run --path ./chroma-data --port 8010
```

Make sure Docker is installed and running on your system.

### Redis Setup

This application uses Redis as the task queue backend for Huey. To run Redis:

```bash
docker run -p 6379:6379 redis:latest
```

If you prefer to use a different Redis configuration, update the `HUEY` settings in your project settings.

### Background Processing with Huey

The CV processing happens in the background using Huey. To start the Huey consumer:

```bash
python manage.py run_huey --workers 5
```

You can adjust the number of workers based on your system's capabilities. More workers allow for more parallel processing of CV files.

## 🔐 Authentication API

### Register a New User

**Endpoint:** `POST /api/register`

**Description:** Register a new user account.

**Request Body:**
```json
{
  "name": "Ismail",
  "email": "ismail@example.com",
  "password": "securePassword123"
}
```

**Response:**
```json
{
  "message": "User registered successfully",
  "user_id": "uuid",
  "token": "jwt_token"
}
```

### Login

**Endpoint:** `POST /api/login`

**Description:** Authenticate a user and receive a JWT token.

**Request Body:**
```json
{
  "email": "ismail@example.com",
  "password": "securePassword123"
}
```

**Response:**
```json
{
  "message": "Login successful",
  "token": "jwt_token",
  "user": {
    "id": "uuid",
    "name": "Ismail",
    "email": "ismail@example.com"
  }
}
```

### Refresh Token

**Endpoint:** `POST /api/token/refresh`

**Description:** Get a new access token using a refresh token.

**Request Body:**
```json
{
  "refresh": "refresh_token"
}
```

**Response:**
```json
{
  "access": "new_access_token"
}
```

## Using JWT Authentication

For protected endpoints, include the JWT token in the Authorization header:

```
Authorization: Bearer <your_jwt_token>
```

## Authentication for Endpoints

For demonstration purposes, the API endpoints are currently configured to allow unauthenticated access. In a production environment, you should enable authentication by modifying the `permission_classes` in `cv/views.py`:

```python
# Change this:
permission_classes = [AllowAny]  # Allow unauthenticated users for demo

# To this:
permission_classes = [IsAuthenticated]  # Require authentication
```

You'll also need to set up authentication tokens or another authentication method through Django REST Framework.

## Testing the API

### Using cURL

To test the CV upload endpoint using cURL, you can use the following command:

```bash
curl -X POST \
  http://127.0.0.1:8000/api/cv/upload/ \
  -F 'file=@/path/to/your/resume.pdf'
```

Replace `/path/to/your/resume.pdf` with the actual path to your PDF file.

### Response Format

A successful upload will return a response like:

```json
{
  "message": "CV uploaded successfully",
  "cv_id": "69a5f72b-445a-4d2f-bcb6-974d022514cd",
  "status": "pending"
}
```

The CV processing happens in the background, and the text will be parsed and stored in ChromaDB.

### Task Checklist

- [x] Upload and parse CV into vectordb

  - [http://localhost:8000/api/cv/upload](http://localhost:8000/api/cv/upload)

- [x] Create get Job Recommendations Endpoint
  - [http://localhost:8000/api/recommendations](http://localhost:8000/api/recommendations)
  - [http://localhost:8000/api/recommendations/?limit=3](http://localhost:8000/api/recommendations/?limit=3)
  
- [x] Implement JWT Authentication
  - [http://localhost:8000/api/register](http://localhost:8000/api/register)
  - [http://localhost:8000/api/login](http://localhost:8000/api/login)
  - [http://localhost:8000/api/token/refresh](http://localhost:8000/api/token/refresh)
