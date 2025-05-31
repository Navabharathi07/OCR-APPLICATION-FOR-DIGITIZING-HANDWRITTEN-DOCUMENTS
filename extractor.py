import streamlit as st
from PIL import Image
import google.generativeai as genai
from pdf2image import convert_from_bytes
import os
import json
import io

# Set up Gemini
genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
model = genai.GenerativeModel("gemini-1.5-flash")

# Poppler path for Windows
POPPLER_PATH = r"C:\Program Files\poppler-24.08.0\Library\bin"

def get_gemini_response(image, prompt):
    # Convert image to bytes for Gemini
    img_byte_arr = io.BytesIO()
    image.save(img_byte_arr, format="PNG")
    img_byte_arr.seek(0)

    # Upload image to Gemini
    uploaded_image = genai.upload_file(img_byte_arr, mime_type="image/png")
    
    # Get response
    response = model.generate_content([uploaded_image, prompt])
    return response.text

# Streamlit UI
st.set_page_config(page_title="OCR", layout="wide")
st.header("OPTICAL CHARACTER RECOGNITION (OCR)")

uploaded_file = st.file_uploader("Upload Image", type=['jpg', 'png', 'jpeg', 'webp'])

col1, col2 = st.columns([1, 1]) 

image = None

if uploaded_file is not None:
    if uploaded_file.type == "application/pdf": 
        st.write("Processing PDF file...")
        try:
            images = convert_from_bytes(uploaded_file.read(), poppler_path=POPPLER_PATH)
            if images:
                with col1:
                    st.image(images[0], caption="First Page of Uploaded PDF", use_column_width=True)
                image = images[0]
            else:
                st.error("No pages found in the PDF.")
        except Exception as e:
            st.error(f"Failed to process PDF: {e}")
    else:  
        image = Image.open(uploaded_file)
        with col1:
            st.image(image, caption="Uploaded Image", use_column_width=True)

# Prompt
prompt = (
"You are an expert manuscript interpreter and JSON data formatter.\n\n"
"Given an image of a handwritten or printed manuscript , perform the following:\n"
"1. Extract the text accurately.\n"
"2. Identify key terms, sentences, or concepts.\n"
"3. For each, provide a simple explanation or meaning.\n"
"4. Return the result in the following structured JSON format:\n\n"
"{\n"
'  "original_text": "full extracted text from the manuscript",\n'
'  "extracted_data": [\n'
"    {\n"
'      "term": "keyword or phrase",\n'
'      "meaning": "its simple explanation"\n'
"    },\n"
"    ...\n"
"  ]\n"
"}\n\n"
"Now process this manuscript image and give your response only in JSON format."
)

# Button to trigger extraction
submit = st.button("Start the Extraction")

if submit and image is not None:
    try:
        response_text = get_gemini_response(image, prompt)

        with col2:
            st.markdown("### 📄 Extracted JSON")
            st.code(response_text, language="json")

        # Validate JSON and download
        try:
            json_data = json.loads(response_text)
            json_str = json.dumps(json_data, indent=2)
        except Exception:
            json_str = response_text  # fallback if not valid JSON

        st.download_button(
            label="📥 Download JSON",
            data=json_str,
            file_name="result.json",
            mime="application/json"
        )

    except Exception as e:
        st.error(f"An error occurred: {e}")
st.markdown("""---\n*Developed by: Sarawin*""")
