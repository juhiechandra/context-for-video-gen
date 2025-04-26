import os
import tempfile
from fastapi import APIRouter, UploadFile, File, HTTPException, BackgroundTasks, Form
from fastapi.responses import JSONResponse, FileResponse
from typing import List

from app.models.schemas import (
    CreateScriptRequest,
    CreateScriptResponse,
    DocumentResponse,
    ErrorResponse,
    DirectScriptGenerationResponse,
    TextToSpeechRequest,
    TextToSpeechResponse
)
from app.utils.helpers import (
    extract_text_from_pdf,
    create_prompt,
    generate_script_with_gemini,
    load_speaker_modes,
    save_generated_script,
    convert_text_to_speech
)

router = APIRouter()


@router.post("/upload_document", response_model=DocumentResponse, responses={400: {"model": ErrorResponse}})
async def upload_document(file: UploadFile = File(...)):
    """
    Upload a PDF document and extract its text content.
    """
    if not file.filename.endswith('.pdf'):
        raise HTTPException(
            status_code=400, detail="Only PDF files are allowed")

    # Create a temporary file to store the uploaded PDF
    with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as temp_file:
        # Write the uploaded file content to the temporary file
        content = await file.read()
        temp_file.write(content)
        temp_file.flush()

        try:
            # Extract text from the PDF
            text_content, page_count = extract_text_from_pdf(temp_file.name)

            if not text_content:
                raise HTTPException(
                    status_code=400, detail="Could not extract text from the PDF. The file might be empty or corrupted.")

            return DocumentResponse(
                content=text_content,
                page_count=page_count,
                status="success"
            )
        except Exception as e:
            raise HTTPException(
                status_code=400, detail=f"Error processing PDF: {str(e)}")
        finally:
            # Clean up the temporary file
            os.unlink(temp_file.name)


@router.post("/create_script", response_model=CreateScriptResponse, responses={400: {"model": ErrorResponse}})
async def create_script(request: CreateScriptRequest):
    """
    Create a script using Gemini based on document content and speaker mode.
    """
    try:
        # Create prompt for Gemini
        prompt = create_prompt(request.document_content, request.speaker_mode)

        # Generate script with Gemini
        script = await generate_script_with_gemini(prompt)

        return CreateScriptResponse(script=script)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error generating script: {str(e)}")


@router.post("/upload_and_generate", response_model=DirectScriptGenerationResponse, responses={400: {"model": ErrorResponse}})
async def upload_and_generate(file: UploadFile = File(...), speaker_mode: str = Form(...)):
    """
    Upload a PDF document and directly generate a script using Gemini.
    Returns the response in JSON format and saves the generated script to a file.
    """
    if not file.filename.endswith('.pdf'):
        raise HTTPException(
            status_code=400, detail="Only PDF files are allowed")

    # Create a temporary file to store the uploaded PDF
    with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as temp_file:
        # Write the uploaded file content to the temporary file
        content = await file.read()
        temp_file.write(content)
        temp_file.flush()

        try:
            # Extract text from the PDF
            text_content, page_count = extract_text_from_pdf(temp_file.name)

            if not text_content:
                raise HTTPException(
                    status_code=400, detail="Could not extract text from the PDF. The file might be empty or corrupted.")

            # Create prompt for Gemini
            prompt = create_prompt(text_content, speaker_mode)

            # Generate script with Gemini
            script = await generate_script_with_gemini(prompt)

            # Save the generated script to a file
            file_path = save_generated_script(
                script, speaker_mode, len(text_content))

            # Return the response with all the required fields
            return DirectScriptGenerationResponse(
                script=script,
                status="success",
                document_length=len(text_content),
                speaker_mode=speaker_mode,
                file_path=file_path
            )
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
        except Exception as e:
            raise HTTPException(
                status_code=500, detail=f"Error processing document or generating script: {str(e)}")
        finally:
            # Clean up the temporary file
            os.unlink(temp_file.name)


@router.get("/speaker_modes", response_model=List[str])
async def get_speaker_modes():
    """
    Get a list of available speaker modes from speaker_modes.json
    """
    try:
        speaker_modes = load_speaker_modes()
        return [mode.get("speaker_mode") for mode in speaker_modes]
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error loading speaker modes: {str(e)}")


@router.post("/text_to_speech", response_model=TextToSpeechResponse, responses={400: {"model": ErrorResponse}})
async def text_to_speech(request: TextToSpeechRequest):
    """
    Convert text to speech using Eleven Labs API
    """
    try:
        # Call the helper function to convert text to speech
        audio_file_path = await convert_text_to_speech(
            text=request.text,
            voice_id=request.voice_id,
            model_id=request.model_id,
            stability=request.stability,
            similarity_boost=request.similarity_boost
        )

        return TextToSpeechResponse(
            audio_file_path=audio_file_path,
            status="success"
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error generating speech: {str(e)}")


@router.post("/text_to_speech/download")
async def text_to_speech_download(request: TextToSpeechRequest):
    """
    Convert text to speech and return the audio file for download
    """
    try:
        # Call the helper function to convert text to speech
        audio_file_path = await convert_text_to_speech(
            text=request.text,
            voice_id=request.voice_id,
            model_id=request.model_id,
            stability=request.stability,
            similarity_boost=request.similarity_boost
        )

        # Return the file for download
        return FileResponse(
            path=audio_file_path,
            filename=os.path.basename(audio_file_path),
            media_type="audio/mpeg"
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error generating speech: {str(e)}")
