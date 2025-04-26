import json
import os
import pdfplumber
import google.generativeai as genai
from dotenv import load_dotenv
from pathlib import Path
import re
import datetime
import asyncio
import uuid
from elevenlabs import generate, save, set_api_key
from elevenlabs.api import Voice, VoiceSettings


# Load environment variables
load_dotenv(Path(__file__).parent.parent / ".env")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY environment variable is not set")

genai.configure(api_key=GEMINI_API_KEY)


def extract_text_from_pdf(file_path: str) -> tuple[str, int]:

    text_content = ""

    with pdfplumber.open(file_path) as pdf:
        page_count = len(pdf.pages)
        for page in pdf.pages:
            text = page.extract_text()
            if text:
                text_content += text + "\n\n"

    return text_content.strip(), page_count


def load_speaker_modes() -> list:

    speaker_modes_path = Path(__file__).parent / "speaker_modes.json"

    with open(speaker_modes_path, "r") as f:
        speaker_modes = json.load(f)

    return speaker_modes


def create_prompt(document_content: str, speaker_mode: str) -> str:

    speaker_modes_list = load_speaker_modes()

    mode_config = None
    for mode in speaker_modes_list:
        if mode.get("speaker_mode") == speaker_mode:
            mode_config = mode
            break

    if not mode_config:
        available_modes = [mode.get("speaker_mode")
                           for mode in speaker_modes_list]
        raise ValueError(
            f"Invalid speaker mode: {speaker_mode}. Available modes: {', '.join(available_modes)}")

    speaker_description = mode_config["content"]

    prompt = f"""
    You are a script generator that will create a script based on the provided document content.
    You should adopt the following speaking style and persona:

    {speaker_description}

    Document Content:
    {document_content}

    IMPORTANT INSTRUCTIONS:
    1. Output ONLY the plain text of the script that will be spoken by our voice agent.
    2. DO NOT include ANY stage directions, music cues, sound effects, or production notes.
    3. DO NOT include special formatting like markdown.
    4. DO NOT use multiple consecutive line breaks (\n\n).
    5. DO NOT include text in parentheses or brackets.
    6. DO NOT include headers, bullet points, or any other formatting.
    7. DO NOT include intro/outro segments that aren't directly related to the content.
    8. Present the content in a natural, conversational way that can be read aloud fluently.
    9. Focus exclusively on the actual words to be spoken.
    10. Use minimal punctuation - only what is necessary for proper reading.
    
    Your output should be clean, plain text that could be fed directly into a text-to-speech system.
    """

    return prompt


async def generate_script_with_gemini(prompt: str) -> str:
    # Assuming you have the appropriate environment variable set
    api_key = os.getenv("GEMINI_API_KEY")

    if not api_key:
        raise ValueError("GEMINI_API_KEY not found in environment variables")

    # Configure genai with your API key
    genai.configure(api_key=api_key)

    # Create the model
    model = genai.GenerativeModel(
        model_name="gemini-1.5-pro",
        generation_config=genai.GenerationConfig(
            temperature=0.7,
            top_p=0.95,
            top_k=40
        )
    )

    try:
        # Generate content
        response = await asyncio.to_thread(model.generate_content, prompt)
        script = response.text
        return script
    except Exception as e:
        raise Exception(f"Error generating content with Gemini: {str(e)}")


def clean_markdown(text: str) -> str:

    # Remove code blocks
    text = re.sub(r'```[\s\S]*?```', '', text)

    # Remove inline code
    text = re.sub(r'`([^`]+)`', r'\1', text)

    # Remove headers
    text = re.sub(r'^#{1,6}\s+', '', text, flags=re.MULTILINE)

    # Remove bold and italic
    text = re.sub(r'\*\*([^*]+)\*\*', r'\1', text)
    text = re.sub(r'\*([^*]+)\*', r'\1', text)
    text = re.sub(r'__([^_]+)__', r'\1', text)
    text = re.sub(r'_([^_]+)_', r'\1', text)

    # Remove bullet points
    text = re.sub(r'^\s*[-*+]\s+', '', text, flags=re.MULTILINE)

    # Remove numbered lists
    text = re.sub(r'^\s*\d+\.\s+', '', text, flags=re.MULTILINE)

    # Remove horizontal rules
    text = re.sub(r'^\s*[-*_]{3,}\s*$', '', text, flags=re.MULTILINE)

    # Remove link syntax
    text = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', text)

    # Remove extra newlines (more than 2 in a row)
    text = re.sub(r'\n{3,}', '\n\n', text)

    return text.strip()


def save_generated_script(script: str, speaker_mode: str, document_length: int) -> str:

    # Create scripts directory if it doesn't exist
    scripts_dir = Path(__file__).parent.parent.parent / "generated_scripts"
    scripts_dir.mkdir(exist_ok=True)

    # Generate timestamp and sanitized filename
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    sanitized_speaker_mode = re.sub(
        r'[^\w\s-]', '', speaker_mode).replace(' ', '_').lower()

    # Generate filename
    filename = f"{timestamp}_{sanitized_speaker_mode}.txt"
    file_path = scripts_dir / filename

    # Clean markdown syntax
    cleaned_script = clean_markdown(script)

    # Write to file
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(cleaned_script)

    return str(file_path)


async def convert_text_to_speech(
    text: str,
    voice_id: str = "21m00Tcm4TlvDq8ikWAM",
    model_id: str = "eleven_multilingual_v2",
    stability: float = 0.5,
    similarity_boost: float = 0.5
) -> str:
    """
    Convert text to speech using Eleven Labs API
    Returns the path to the generated audio file
    """
    # Ensure the API key is set
    api_key = os.getenv("ELEVENLABS_API_KEY")
    if not api_key:
        raise ValueError(
            "ELEVENLABS_API_KEY not found in environment variables")

    set_api_key(api_key)

    # Create output directory if it doesn't exist
    output_dir = os.path.join(os.getcwd(), "generated_audio")
    os.makedirs(output_dir, exist_ok=True)

    # Generate a unique filename
    filename = f"{uuid.uuid4()}.mp3"
    output_path = os.path.join(output_dir, filename)

    try:
        # Generate audio
        voice_settings = VoiceSettings(
            stability=stability,
            similarity_boost=similarity_boost
        )

        audio = await asyncio.to_thread(
            generate,
            text=text,
            voice=Voice(
                voice_id=voice_id,
                settings=voice_settings
            ),
            model=model_id
        )

        # Save audio to file
        await asyncio.to_thread(save, audio, output_path)

        return output_path
    except Exception as e:
        raise Exception(f"Error generating speech with Eleven Labs: {str(e)}")
