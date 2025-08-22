import streamlit as st
import requests
from bs4 import BeautifulSoup
from PyPDF2 import PdfReader
import cv2
import numpy as np
import fitz
from PIL import Image
import io
import re
import math
from transformers import AutoTokenizer # Requires 'transformers' library
import time # Used for simulating delay if needed, or just for general time-based ops


# ONLY ADDED: Import the common sidebar renderer from auth_utils
from auth_utils.firebase_manager import render_sidebar_profile


# --- Streamlit Configuration ---
st.set_page_config(
            page_title="Text Extraction",
            layout="centered"
        )

# ONLY ADDED: Call the common sidebar profile renderer at the very beginning of the script
render_sidebar_profile()


# Removing Streamlit's Tripple dot (using markdown) and hiding the menu (PRESERVED - NO CHANGES)
st.markdown('''
<style>
.stMainMenu, .st-emotion-cache-weq6zh.em9zgd017 {
    visibility: hidden;
}
img {
    border-radius: 15px;
}
</style>
''', unsafe_allow_html= True)


# --- Configuration for LLMs (PRESERVED - NO CHANGES) ---
try:
    HF_API_TOKEN = st.secrets["huggingface"]["api_token"]
    # OR if using api_keys structure:
    # HF_API_TOKEN = st.secrets["api_keys"]["huggingface"]
except KeyError:
    st.error("❌ Hugging Face API token not found in secrets. Please add it to .streamlit/secrets.toml")
    st.stop()
KIMI_K2_CHAT_API_URL = "https://router.huggingface.co/v1/chat/completions"
BART_SUMMARIZATION_API_URL = "https://router.huggingface.co/hf-inference/models/facebook/bart-large-cnn"
BGE_EMBEDDING_API_URL = "https://router.huggingface.co/hf-inference/models/BAAI/bge-small-en-v1.5/pipeline/feature-extraction"

HEADERS_CHAT = {
    "Authorization": f"Bearer {HF_API_TOKEN}",
    "Content-Type": "application/json"
}
HEADERS_EMBEDDING = {
    "Authorization": f"Bearer {HF_API_TOKEN}",
    "Content-Type": "application/json"
}

# --- Constants for Body Summary (PRESERVED - NO CHANGES) ---
MODEL_MAX_TOKENS = 1024
SAFETY_BUFFER = 50
MAX_RECURSION_DEPTH = 3

# --- Global Tokenizer for BART (now lazy-loaded, still cached) ---
@st.cache_resource
def load_bart_tokenizer_cached(): # Renamed for clarity in lazy loading
    try:
        return AutoTokenizer.from_pretrained("facebook/bart-large-cnn")
    except Exception as e:
        print(f"Error initializing BART tokenizer: {e}")
        return None

# The tokenizer is NOT loaded here anymore. It will be loaded when needed.
# bart_tokenizer = load_bart_tokenizer() # REMOVED


# --- Text Cleaning and Preparation Function (PRESERVED - NO CHANGES) ---
def clean_and_prepare_text(raw_text: str) -> tuple[str, list[str]]:
    """
    Cleans raw text and prepares it for summarization by normalizing whitespace,
    removing common boilerplate, and tokenizing into sentences using rule-based regex.

    Args:
        raw_text: The input text (e.g., from a 3-5 page write-up).

    Returns:
        A tuple containing:
        - cleaned_text: The entire document as a single, cleaned string.
        - original_sentences: A list of original sentences extracted from the cleaned text.
        These sentences retain their original phrasing for extractive tasks.
    """
    if not isinstance(raw_text, str) or not raw_text.strip():
        print("Warning: Input text is empty or not a string. Returning empty values.")
        return "", []

    # --- Step 1: Initial Whitespace Normalization ---
    temp_cleaned_text = re.sub(r'\s+', ' ', raw_text).strip()

    # --- Step 2: Normalize Newlines for Paragraphs ---
    temp_cleaned_text = re.sub(r'(\n\s*){2,}', '@@PARAGRAPH_BREAK@@', temp_cleaned_text)
    temp_cleaned_text = temp_cleaned_text.replace('\n', ' ')
    cleaned_text = temp_cleaned_text.replace('@@PARAGRAPH_BREAK@@', '\n\n')

    # --- Step 3: Remove Common Boilerplate/Noise ---
    cleaned_text = re.sub(r'(\bPage\s+\d+\s+of\s+\d+\b|\b\d+\s+of\s+\d+\b|\s+-\s*\d+\s*-\s*|\s+\d+\s+)', '', cleaned_text, flags=re.IGNORECASE)
    cleaned_text = re.sub(r'https?://\S+|www\.\S+', '', cleaned_text)
    cleaned_text = re.sub(r'\S+@\S+', '', cleaned_text)
    cleaned_text = re.sub(r'©\s*\d{4}.*|Copyright\s*©?.*', '', cleaned_text, flags=re.IGNORECASE)
    cleaned_text = re.sub(r'[^\w\s\.\,\;\:\?\!\-\'\(\)\"\`]', '', cleaned_text)

    # --- Step 4: Final Whitespace Normalization ---
    cleaned_text = re.sub(r'\s{2,}', ' ', cleaned_text).strip()

    # --- Step 5: Rule-Based Sentence Tokenization (NO DOWNLOADS) ---
    temp_sentences = re.split(r'(?<=[.!?])\s+', cleaned_text)
    cleaned_sentences = []
    for sentence in temp_sentences:
        s = sentence.strip()
        if s:
            cleaned_sentences.append(s)

    return cleaned_text, cleaned_sentences


# --- Helper Functions (for summarization - PRESERVED - NO CHANGES) ---
def _split_into_sentences(text):
    """Splits a text into sentences using a simple regex-based approach."""
    sentences = re.split(r'(?<=[.!?])\s+', text)
    return [s.strip() for s in sentences if s.strip()]

def _count_words(text):
    """Counts the number of words in a given text."""
    return len(text.split())

def _cosine_similarity(vec1, vec2):
    """Calculates the cosine similarity between two vectors."""
    dot_product = sum(v1 * v2 for v1, v2 in zip(vec1, vec2))
    magnitude1 = math.sqrt(sum(v**2 for v in vec1))
    magnitude2 = math.sqrt(sum(v**2 for v in vec2))
    if not magnitude1 or not magnitude2:
        return 0.0
    return dot_product / (magnitude1 * magnitude2)

def _query_kimi_k2(payload):
    """Sends a request to the Kimi-K2-Instruct model via Hugging Face Router."""
    try:
        response = requests.post(KIMI_K2_CHAT_API_URL, headers=HEADERS_CHAT, json=payload, timeout=60)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        if hasattr(e, 'response') and e.response is not None and e.response.status_code == 400:
            print("Payload too large or bad request for Kimi-K2.")
        return None

def _query_bart_api(payload):
    """Robust API query for BART with error handling"""
    try:
        response = requests.post(BART_SUMMARIZATION_API_URL, headers=HEADERS_CHAT, json=payload, timeout=60)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        if hasattr(e, 'response') and e.response is not None and e.response.status_code == 400:
            print("Payload too large or bad request for BART.")
        return None

def _get_bge_embeddings(sentences):
    """Gets embeddings for a list of sentences using BAAI/bge-small-en-v1.5 model."""
    payload = {
        "inputs": sentences,
        "parameters": {
            "wait_for_model": True
        }
    }
    try:
        response = requests.post(BGE_EMBEDDING_API_URL, headers=HEADERS_EMBEDDING, json=payload, timeout=60)
        response.raise_for_status()
        embeddings = response.json()
        if isinstance(embeddings, list) and all(isinstance(e, list) for e in embeddings):
            return embeddings
        else:
            return None
    except requests.exceptions.RequestException as e:
        if hasattr(e, 'response') and e.response is not None and e.response.status_code == 400:
            print("Payload too large or bad request for BGE embeddings.")
        return None
    except Exception as e:
        return None

def _get_kimi_k2_abstractive_summary_for_outline(text, prompt_instruction, num_sentences_target):
    """Generates an abstractive summary (Key Discoveries) using Kimi-K2-Instruct for the outline section."""
    user_prompt = f"{prompt_instruction}\n\nText: {text}"
    payload = {
        "messages": [
            {
                "role": "user",
                "content": user_prompt
            }
        ],
        "model": "moonshotai/Kimi-K2-Instruct:novita",
        "temperature": 0.7,
        "max_tokens": num_sentences_target * 30,
        "stop": ["\n\n", "---", "###", "##", "#"]
    }
    try:
        response_data = _query_kimi_k2(payload)
        if response_data:
            generated_content = response_data["choices"][0]["message"]["content"].strip()
            generated_sentences = _split_into_sentences(generated_content)
            filtered_sentences = [
                s for s in generated_sentences
                if not s.lower().startswith(prompt_instruction.lower().split('\n')[0].split(':')[0])
            ]
            return filtered_sentences[:num_sentences_target]
        else:
            return []
    except Exception as e:
        return []

# --- Main Summarization Functions (MODIFIED for lazy tokenizer loading) ---
def generate_heading_summary(text_to_summarize):
    """Generates a suitable heading for the given text using Kimi-K2-Instruct."""
    user_prompt = (
        """In 2 - 10 word, what is the main topic of the following write up:"""
        f"{text_to_summarize}"
    )
    payload = {
        "messages": [
            {
                "role": "user",
                "content": user_prompt
            }
        ],
        "model": "moonshotai/Kimi-K2-Instruct:novita",
        "temperature": 0.7,
        "max_tokens": 20,
        "stop": ["\n", ".", "!", "?"]
    }
    try:
        response_data = _query_kimi_k2(payload)
        if response_data:
            generated_content = response_data["choices"][0]["message"]["content"].strip()
            generated_content = generated_content.strip('.,!?;:"\' ')
            return generated_content
        else:
            return "Failed to generate heading."
    except Exception as e:
        return f"Error generating heading: {e}"

def generate_body_summary(text: str, target_length: tuple = (150, 250), current_depth: int = 0):
    """Recursively summarizes text with strict token limits using BART."""
    # MODIFIED: Get tokenizer from the cached function, which will now be called inside the button block
    bart_tokenizer_instance = load_bart_tokenizer_cached() 
    if bart_tokenizer_instance is None:
        return "Error: BART tokenizer not initialized. Cannot generate body summary."

    min_tokens = math.ceil(target_length[0] * 1.3)
    max_tokens = min(math.floor(target_length[1] * 1.3), MODEL_MAX_TOKENS - SAFETY_BUFFER)
    encoded = bart_tokenizer_instance(text, return_tensors="pt", truncation=False) # Use instance
    token_count = encoded['input_ids'].shape[1]

    if token_count <= MODEL_MAX_TOKENS - SAFETY_BUFFER:
        result = _query_bart_api({
            "inputs": text,
            "parameters": {
                "max_length": max_tokens,
                "min_length": min_tokens,
                "do_sample": False
            }
        })
        if result is None:
            return "Failed to get a summary from the BART API."
        return result[0]['summary_text'] if result and len(result) > 0 and 'summary_text' in result[0] else "Failed to get summary text from BART."

    if current_depth >= MAX_RECURSION_DEPTH:
        return "Max recursion depth reached for body summary."

    chunk_size = 800
    overlap = 100
    tokens = bart_tokenizer_instance.encode(text, add_special_tokens=False) # Use instance
    chunks = []
    for i in range(0, len(tokens), chunk_size - overlap):
        chunk = tokens[i:i + chunk_size]
        chunks.append(bart_tokenizer_instance.decode(chunk)) # Use instance

    intermediate = []
    for chunk in chunks:
        chunk_result = _query_bart_api({
            "inputs": chunk,
            "parameters": {
                "max_length": 100,
                "min_length": 20,
                "do_sample": False
            }
        })
        if chunk_result is None:
            return "Failed to get an intermediate summary from the BART API during chunking."

        if chunk_result and len(chunk_result) > 0 and 'summary_text' in chunk_result[0]:
            intermediate.append(chunk_result[0]['summary_text'])

    if not intermediate:
        return "No intermediate summaries generated."

    return generate_body_summary(" ".join(intermediate), target_length, current_depth + 1)

def generate_outline_summary(cleaned_text):
    """Generates a structured outline summary based on the cleaned, unsummarized text."""
    outline = {
        "Main Points": [],
        "Key Discoveries": []
    }
    word_count = _count_words(cleaned_text)

    if 400 <= word_count <= 1200:
        num_main_points = 3
        num_key_discoveries = 4
    elif 1201 <= word_count <= 2000:
        num_main_points = 5
        num_key_discoveries = 5
    else:
        num_main_points = 5
        num_key_discoveries = 5

    sentences = _split_into_sentences(cleaned_text)
    if not sentences:
        outline["Main Points"] = ["Error: No sentences found for main points."]
    else:
        embeddings = _get_bge_embeddings(sentences)
        if embeddings is None or not embeddings:
            outline["Main Points"] = ["Error: Failed to get embeddings for main points."]
        else:
            doc_centroid = [sum(col) / len(col) for col in zip(*embeddings)]
            sentence_scores = []
            for i, sentence_embedding in enumerate(embeddings):
                score = _cosine_similarity(sentence_embedding, doc_centroid)
                sentence_scores.append((score, sentences[i]))
            sentence_scores.sort(key=lambda x: x[0], reverse=True)
            outline["Main Points"] = [s[1] for s in sentence_scores[:num_main_points]]

    key_discoveries_prompt = (
            f"""Read the following text and generate {num_key_discoveries} interesting or important facts, insights, or discoveries, each between 11 to 15 words long.
            Each sentence should:
            Clearly state a noteworthy idea, discovery, or surprising point or fact from the text;
            Be based on the most interested or meaningful points in the text;
            Be simple, clear, and easy to remember;
            Use language that remains close to the original, but not copied verbatim;
            Do not include any introductory phrases like 'Key discoveries include:' or 'The main findings are:';
            Just provide the sentences directly.
            """
    )
    outline["Key Discoveries"] = _get_kimi_k2_abstractive_summary_for_outline(
        cleaned_text, key_discoveries_prompt, num_key_discoveries
    )
    return outline

def summarize_document(raw_text: str):
    """
    Generates a full summary (Heading, Body, Outline) for a given document.
    The raw_text is first cleaned using the comprehensive regex cleaning function.
    """
    cleaned_text, _ = clean_and_prepare_text(raw_text)
    if not cleaned_text.strip():
        return {"error": "Input text is empty or contains only whitespace after cleaning."}

    heading = generate_heading_summary(cleaned_text)
    body_summary = generate_body_summary(cleaned_text)
    if not body_summary:
        body_summary = "Failed to generate body summary."

    outline_summary = generate_outline_summary(cleaned_text)

    full_summary = {
        "Heading": heading,
        "Body Summary": body_summary,
        "Outline Summary": outline_summary
    }

    return full_summary


# --- Core Functions (for text extraction) ---
def fetch_url_content(url):
    """Extract main text content from a URL"""
    try:
        if not url.startswith(('http://', 'https://')) and not url.startswith('file://'):
            url = 'https://' + url

        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }

        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, 'html.parser')

        for element in soup(['script', 'style', 'nav', 'footer', 'iframe', 'noscript']):
            element.decompose()

        text = ' '.join([p.get_text(strip=True, separator=' ') for p in soup.find_all(['p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'article'])])
        return text if text.strip() else "No main content found (may requires JavaScript rendering)"
    except Exception as e:
        return f"Error: {str(e)}"


# PDF Parser
def extract_pdf_text(pdf_file):
    """Extract text from searchable PDFs"""
    try:
        reader = PdfReader(pdf_file)
        full_text = ""
        for page in reader.pages:
            full_text += page.extract_text() or ""
        return full_text
    except Exception as e:
        return f"Error reading PDF: {str(e)}"



# --- Main Page UI and Logic ---
def main():
    
    st.write("<h3 style='text-align:center; font-size: 32px; font-weight: bold;'>📝 Text Extraction</h3>", unsafe_allow_html=True)
    st.write("<p style='text-align: center; font-size: 14px;'>Extract text from a website, PDF; or paste text directly</p>", unsafe_allow_html=True)
    st.write('---')

    # Initialize session state variables (preserved - NO CHANGES)
    if 'extracted_text' not in st.session_state:
        st.session_state['extracted_text'] = ""
    if 'summary_output' not in st.session_state:
        st.session_state['summary_output'] = None
        
    # Tabbed interface for input sources (preserved - NO CHANGES)
    tab_text, tab_url, tab_pdf = st.tabs(["Paste Text", "URL", "PDF"])

    with tab_text:
        text = st.text_area(
            "Write something!",
            placeholder= 'paste your text here...',
            height=300,
            key='text_area_key')
        if st.button('Use text'):
            st.session_state['extracted_text'] = text
            st.toast('Ready to generate summary')

    with tab_url:
        url_input = st.text_input("Enter that URL!", placeholder= 'paste your link here...')
        if st.button("Fetch from URL"):
            if url_input:
                with st.spinner("Fetching content..."):
                    fetched_content = fetch_url_content(url_input)
                if "Error" in fetched_content or "No main content" in fetched_content:
                    st.error(fetched_content)
                    st.session_state['extracted_text'] = ""
                else:
                    st.session_state['extracted_text'] = fetched_content
                    # Display the fetched content in a text_area within this tab
                    st.text_area(label= 'Web Content', value= fetched_content, height= 300, key="url_content_display")
                    st.toast('Ready to generate full summary')
            else:
                st.warning("Please enter a URL.")


    with tab_pdf:
        pdf_file = st.file_uploader("Upload a PDF file:", type=["pdf"])
        if pdf_file:
            # if st.button("Extract from PDF"): # Removed the button for PDF as it triggers automatically on upload now
            with st.spinner("Extracting text from PDF..."):
                pdf_content = extract_pdf_text(pdf_file)
            if not pdf_content.strip():
                st.error("Failed to extract any text from the PDF.")
                st.session_state['extracted_text'] = ""
            else:
                st.session_state['extracted_text'] = pdf_content
                # Display the extracted PDF content in a text_area within this tab
                st.text_area(label= 'PDF Content', value= pdf_content, height= 300, key="pdf_content_display")
                st.toast('Ready to generate summary')

    # --- Summarization Logic (MODIFIED for lazy tokenizer loading) ---
    if st.button("📋 Generate Your Summary", key="generate_summary_button", width= "stretch"):
        if st.session_state['extracted_text'] and st.session_state['extracted_text'].strip():
            length = len(st.session_state['extracted_text'].split())
            if length < 400:
                st.toast(f'{length}/400 words; Writing too short!')
            else:
                with st.spinner("Generating Summary! Be done in a moment:)..."):
                    # MODIFIED: Load the tokenizer here, within the spinner
                    global bart_tokenizer # Declare global to modify the variable
                    if 'bart_tokenizer_instance' not in st.session_state:
                        st.session_state['bart_tokenizer_instance'] = load_bart_tokenizer_cached()
                    bart_tokenizer = st.session_state['bart_tokenizer_instance'] # Assign to global for function use

                    summary_output = summarize_document(st.session_state['extracted_text'])
                    st.session_state['summary_output'] = summary_output
                st.success("Summary generated successfully!")
                st.switch_page("pages/3_SummaReader.py")
        else:
            st.warning("Please provide some text to summarize.")



if __name__ == "__main__":
    main()




