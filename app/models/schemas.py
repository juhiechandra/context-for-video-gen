from pydantic import BaseModel, Field
from typing import Optional


class CreateScriptRequest(BaseModel):
    document_content: str = Field(...,
                                  description="The extracted text from the PDF document")
    speaker_mode: str = Field(...,
                              description="Mode setting based on a local JSON file")


class CreateScriptResponse(BaseModel):
    script: str = Field(..., description="The generated script from Gemini")


class DocumentResponse(BaseModel):
    content: str = Field(...,
                         description="The extracted text content from the document")
    page_count: int = Field(...,
                            description="The number of pages in the document")
    status: str = Field(default="success",
                        description="Status of the operation")


class ErrorResponse(BaseModel):
    detail: str = Field(..., description="Error detail message")
    status: str = Field(default="error", description="Status of the operation")


class DirectScriptGenerationResponse(BaseModel):
    script: str = Field(..., description="The generated script from Gemini")
    status: str = Field(default="success",
                        description="Status of the operation")
    model: str = Field(default="gemini-1.5-pro",
                       description="The model used for generation")
    document_length: int = Field(...,
                                 description="Number of characters in the source document")
    speaker_mode: str = Field(...,
                              description="The speaker mode used for generation")
    file_path: str = Field(..., description="Path to the saved script file")


class TextToSpeechRequest(BaseModel):
    text: str = Field(..., description="Text to convert to speech")
    voice_id: str = Field(default="21m00Tcm4TlvDq8ikWAM",
                          description="Voice ID from Eleven Labs")
    model_id: str = Field(default="eleven_multilingual_v2",
                          description="Model ID from Eleven Labs")
    stability: float = Field(default=0.5, description="Voice stability (0-1)")
    similarity_boost: float = Field(
        default=0.5, description="Voice similarity boost (0-1)")


class TextToSpeechResponse(BaseModel):
    audio_file_path: str = Field(...,
                                 description="Path to the generated audio file")
    status: str = Field(default="success",
                        description="Status of the operation")
