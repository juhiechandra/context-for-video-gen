import os
import json
import tempfile
import streamlit as st
import requests
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv(Path(__file__).parent / ".env")

# Set page configuration
st.set_page_config(
    page_title="LearnTube Script Generator",
    page_icon="📝",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Load speaker modes


def load_speaker_modes():
    speaker_modes_path = Path(__file__).parent / "utils" / "speaker_modes.json"
    with open(speaker_modes_path, "r") as f:
        return json.load(f)

# Main function


def main():
    # Initialize session state variables to prevent KeyError
    if "document_content" not in st.session_state:
        st.session_state.document_content = ""
    if "page_count" not in st.session_state:
        st.session_state.page_count = 0
    if "generated_script" not in st.session_state:
        st.session_state.generated_script = ""
    if "selected_mode" not in st.session_state:
        st.session_state.selected_mode = ""

    # Add header and description
    st.title("📝 LearnTube Script Generator")
    st.markdown("""
    Upload a PDF document, select a speaker mode, and generate a script using Gemini 2.0 Flash.
    """)

    # Sidebar for API configuration
    with st.sidebar:
        st.header("About")
        st.info("""
        This application uses FastAPI backend with Gemini 2.0 Flash to generate scripts from PDF documents.
        """)

        st.header("API Configuration")
        api_url = st.text_input("API URL", value="http://localhost:8000/api")

        # Display available speaker modes
        st.header("Available Speaker Modes")
        speaker_modes = load_speaker_modes()
        for mode_data in speaker_modes:
            mode_name = mode_data.get("speaker_mode")
            with st.expander(f"{mode_name}"):
                st.write(mode_data["content"][:500] + "...")

    # Create tabs
    tab1, tab2 = st.tabs(["Upload Document", "Generated Script"])

    # Tab 1: Upload Document
    with tab1:
        st.header("Upload PDF Document")
        uploaded_file = st.file_uploader("Choose a PDF file", type="pdf")

        if uploaded_file is not None:
            # Display file details
            file_details = {
                "Filename": uploaded_file.name,
                "File size": f"{uploaded_file.size / 1024:.2f} KB"
            }
            st.json(file_details)

            # Create a temporary file
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_file:
                temp_file.write(uploaded_file.getvalue())
                temp_file_path = temp_file.name

            try:
                # Upload to API
                with st.spinner("Extracting text from PDF..."):
                    files = {"file": (uploaded_file.name, open(
                        temp_file_path, "rb"), "application/pdf")}
                    response = requests.post(
                        f"{api_url}/upload_document", files=files)

                    if response.status_code == 200:
                        pdf_data = response.json()
                        st.session_state.document_content = pdf_data["content"]
                        st.session_state.page_count = pdf_data["page_count"]

                        # Show success message
                        st.success(
                            f"Successfully extracted text from {pdf_data['page_count']} pages.")

                        # Display extracted text
                        with st.expander("View Extracted Text"):
                            st.text_area(
                                "Content", value=st.session_state.document_content, height=300, disabled=True)

                        # Select speaker mode
                        speaker_mode_options = [
                            mode.get("speaker_mode") for mode in speaker_modes]
                        speaker_mode = st.selectbox(
                            "Select Speaker Mode",
                            options=speaker_mode_options
                        )

                        # Generate script button
                        if st.button("Generate Script"):
                            with st.spinner("Generating script with Gemini..."):
                                # Call API to generate script
                                script_response = requests.post(
                                    f"{api_url}/create_script",
                                    json={
                                        "document_content": st.session_state.document_content,
                                        "speaker_mode": speaker_mode
                                    }
                                )

                                if script_response.status_code == 200:
                                    script_data = script_response.json()
                                    st.session_state.generated_script = script_data["script"]
                                    st.session_state.selected_mode = speaker_mode

                                    # Show success message and switch to tab 2
                                    st.success(
                                        "Script generated successfully!")
                                    st.balloons()
                                    # Use JavaScript to switch to the second tab
                                    js = f"""
                                    <script>
                                        window.parent.document.querySelectorAll('.stTabs button')[1].click();
                                    </script>
                                    """
                                    st.components.v1.html(js)
                                else:
                                    st.error(
                                        f"Error generating script: {script_response.text}")
                    else:
                        st.error(f"Error extracting text: {response.text}")
            except Exception as e:
                st.error(f"Error: {str(e)}")
            finally:
                # Clean up the temporary file
                os.unlink(temp_file_path)

    # Tab 2: Generated Script
    with tab2:
        st.header("Generated Script")

        if st.session_state.generated_script:
            st.subheader(
                f"Mode: {st.session_state.selected_mode.capitalize()}")

            # Display the generated script
            st.markdown(st.session_state.generated_script)

            # Add download button
            st.download_button(
                label="Download Script",
                data=st.session_state.generated_script,
                file_name=f"{st.session_state.selected_mode}_script.md",
                mime="text/markdown"
            )
        else:
            st.info(
                "Upload a document and generate a script to see the results here.")


if __name__ == "__main__":
    main()
