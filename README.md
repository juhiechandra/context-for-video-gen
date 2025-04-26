# LearnTube API

A FastAPI backend for document processing and script generation using Gemini 2.0 Flash model.

## Features

- Upload PDF documents and extract text content
- Generate scripts from document content using different speaker modes
- Integration with Google's Gemini 2.0 Flash model
- Text-to-speech conversion using Eleven Labs API

## Project Structure

```
learn-tube/
├── app/
│   ├── api/
│   │   └── routes.py         # API endpoints
│   ├── models/
│   │   └── schemas.py        # Pydantic models
│   ├── utils/
│   │   ├── helpers.py        # Utility functions
│   │   └── speaker_modes.json # Speaker mode configurations
│   ├── .env                  # Environment variables
│   └── main.py              # Main application
└── requirements.txt         # Dependencies
```

## Setup

1. Clone the repository:

```bash
git clone <repository-url>
cd learn-tube
```

2. Create a virtual environment and activate it:

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:

```bash
pip install -r requirements.txt
```

4. Set up your Gemini API key:
   - Get an API key from [Google AI Studio](https://ai.google.dev/)
   - Update the `.env` file in the `app` directory with your API key:

     ```
     GEMINI_API_KEY=your_gemini_api_key_here
     ```

5. Set up your Eleven Labs API key:
   - Get an API key from [Eleven Labs](https://elevenlabs.io/)
   - Add it to your `.env` file in the `app` directory:

     ```
     ELEVENLABS_API_KEY=your_elevenlabs_api_key_here
     ```

## Running the API

Start the FastAPI server:

```bash
cd learn-tube
python -m app.main
```

The API will be available at <http://localhost:8000>

## API Endpoints

### 1. Upload Document

**Endpoint:** `POST /api/upload_document`

**Description:** Upload a PDF document and extract its text content.

**Request:**

- Form data with a file field named `file` containing the PDF document.

**Response:**

```json
{
  "content": "Extracted text from the PDF",
  "page_count": 5,
  "status": "success"
}
```

### 2. Create Script

**Endpoint:** `POST /api/create_script`

**Description:** Create a script using Gemini based on document content and speaker mode.

**Request:**

```json
{
  "document_content": "Extracted text from the PDF",
  "speaker_mode": "educational"
}
```

**Response:**

```json
{
  "script": "Generated script from Gemini"
}
```

### 3. Text-to-Speech Conversion

**Endpoint:** `POST /api/text_to_speech`

**Description:** Convert text to speech using Eleven Labs API.

**Request:**

```json
{
  "text": "Text to convert to speech",
  "voice_id": "21m00Tcm4TlvDq8ikWAM", // Optional: Default is the "Rachel" voice
  "model_id": "eleven_multilingual_v2", // Optional: Default is multilingual model
  "stability": 0.5, // Optional: Voice stability (0-1)
  "similarity_boost": 0.5 // Optional: Voice similarity boost (0-1)
}
```

**Response:**

```json
{
  "audio_file_path": "/path/to/generated/audio.mp3",
  "status": "success"
}
```

### 4. Text-to-Speech with Download

**Endpoint:** `POST /api/text_to_speech/download`

**Description:** Convert text to speech and return the audio file for download.

**Request:** Same as the text_to_speech endpoint.

**Response:** Audio file download (MP3 format).

## Available Speaker Modes

- `educational`: Creates an educational script with clear explanations
- `conversational`: Transforms content into a conversational script with dialogue
- `professional`: Converts content into a formal, professional script

## Documentation

API documentation is available at <http://localhost:8000/docs> when the server is running.
