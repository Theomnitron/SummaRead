import streamlit as st
import base64
from io import BytesIO
from gtts import gTTS
import time
from fpdf import FPDF # Import for PDF generation

# Import the common sidebar renderer from auth_utils
from auth_utils.firebase_manager import render_sidebar_profile

st.set_page_config(layout="centered",
                page_icon="🗣️",
                page_title="Text to Speech")

# Call the common sidebar profile renderer at the very beginning of the script
render_sidebar_profile()

# Add the 'Open-Dyslexic' font and custom CSS
st.markdown('''
<style>
@import url('https://fonts.googleapis.com/css2?family=Open+Dyslexic:wght@400;700&display=swap');

/* Main Streamlit style overrides */
.stMainMenu, .st-emotion-cache-weq6zh.em9zgd017 {
    visibility: hidden;
}

/* Apply Open-Dyslexic to the entire document body */
body, .open-dyslexic {
    font-family: 'Open-Dyslexic', sans-serif !important;
}

/* Specific styling for summary components */
.heading-summary {
    font-family: 'Open-Dyslexic', sans-serif !important;
    font-size: 2.5em; /* Adjusted to be very big */
    font-weight: 700;
    text-align: center;
    margin-top: 20px;
    margin-bottom: 20px;
}
.body-summary {
    font-family: 'Open-Dyslexic', sans-serif !important;
    font-size: 1em; /* Kept normal size */
    line-height: 1.6;
}
.outline-summary {
    font-family: 'Open-Dyslexic', sans-serif !important;
    font-size: 1em;
}
.outline-summary ul {
    list-style-type: disc;
    padding-left: 20px;
}
.outline-summary li {
    margin-bottom: 8px;
    padding-left: 10px; /* Indentation for bullet points */
}

/* Footer styling (kept as is for audio player) */
.fixed-footer {
    position: fixed;
    bottom: 0;
    left: 0;
    right: 0;
    background: rgba(0, 0, 0, 0);
    padding-left: 15px;
    padding-right: 15px;
    border-radius: 2rem;
    box-shadow: 0 -2px 10px rgba(0, 0, 0, 0);
    z-index: 1000;
}
/* Removed .floating-download-button-container and .floating-download-button CSS */
</style>
''', unsafe_allow_html= True)


# --- PDF Generation Function (Cached) ---
@st.cache_data
def generate_summary_pdf_bytes(summary_data):
    pdf = FPDF()
    pdf.add_page()
    
    # Set up basic font for the whole document
    pdf.set_font("Arial", size=12) # Arial is a standard font in FPDF

    # --- Heading ---
    pdf.set_font("Arial", 'B', 20) # Bold, larger font for heading
    pdf.multi_cell(0, 10, summary_data['Heading'], align='C') # Centered heading
    pdf.ln(15) # Add more space after heading

    # --- Body Summary ---
    pdf.set_font("Arial", size=12) # Reset to normal font for body
    pdf.multi_cell(0, 8, summary_data['Body Summary']) # Body text with line wrapping
    pdf.ln(10) # Add space after body

    # --- Outline Summary ---
    pdf.set_font("Arial", 'B', 14) # Bold, slightly larger for "Important Points"
    pdf.cell(0, 10, "Important Points:", ln=True)
    pdf.ln(2)

    # Main Points
    pdf.set_font("Arial", size=12) # Normal font for bullet points
    for point in summary_data['Outline Summary']['Main Points']:
        pdf.set_x(10) # Reset x position for bullet
        pdf.cell(5, 8, txt="•", ln=0) # Bullet point
        # Use multi_cell for the text part, starting from an indented position
        pdf.set_x(pdf.get_x() + 5) # Indent text slightly after bullet
        pdf.multi_cell(pdf.get_page_width() - 30, 8, txt=point, align='L')
        pdf.ln(1) # Small line break after each point

    pdf.ln(5) # Space between main points and key discoveries

    # Key Discoveries
    pdf.set_font("Arial", 'B', 14) # Bold, slightly larger for "Key Discoveries"
    pdf.cell(0, 10, "Key Discoveries:", ln=True)
    pdf.ln(2)

    pdf.set_font("Arial", size=12) # Normal font for bullet points
    for discovery in summary_data['Outline Summary']['Key Discoveries']:
        pdf.set_x(10) # Reset x position for bullet
        pdf.cell(5, 8, txt="•", ln=0) # Bullet point
        # Use multi_cell for the text part, starting from an indented position
        pdf.set_x(pdf.get_x() + 5) # Indent text slightly after bullet
        pdf.multi_cell(pdf.get_page_width() - 30, 8, txt=discovery, align='L')
        pdf.ln(1) # Small line break after each point

    return pdf.output(dest='S').encode('latin1') # Output PDF as bytes, encoded to latin1 for fpdf

# Main content container
main_container = st.container()
footer_container = st.container()

# Wrap the entire main content in a logged-in check
if st.session_state.get('logged_in', False):
    with main_container:
        st.write("<h3 style='text-align:center'>🗣️ Summary Reader</h3>", unsafe_allow_html=True)
        
        # Check if the summary exists in session state
        if 'summary_output' in st.session_state and st.session_state['summary_output'] is not None:
            summary = st.session_state['summary_output']

            # Display the heading with the biggest font-size and center alignment
            st.markdown(f"<h2 class='heading-summary'>{summary['Heading']}</h2>", unsafe_allow_html=True)

            st.write('---')

            # Display the body summary with the custom font
            st.markdown(f"<p class='body-summary'>{summary['Body Summary']}</p>", unsafe_allow_html=True)

            st.write('---')

            # Display the outline summary with bullet points and indentation
            st.markdown('<h5 class="open-dyslexic">Important Points:</h5>', unsafe_allow_html= True)
            
            # Main Points
            st.markdown("<ul class='outline-summary'>", unsafe_allow_html=True)
            for point in summary['Outline Summary']['Main Points']:
                st.markdown(f"<li>{point}</li>", unsafe_allow_html=True)
            st.markdown("</ul>", unsafe_allow_html=True)

            # Key Discoveries
            st.markdown("<h5 class='open-dyslexic'>Key Discoveries:</h5>", unsafe_allow_html=True)
            st.markdown("<ul class='outline-summary'>", unsafe_allow_html=True)
            for discovery in summary['Outline Summary']['Key Discoveries']:
                st.markdown(f"<li>{discovery}</li>", unsafe_allow_html=True)
            st.markdown("</ul>", unsafe_allow_html=True)

            # --- Construct the full summary text for TTS ---
            full_summary_text_for_tts = (
                summary['Heading'] + "\n\n" +
                summary['Body Summary'] + "\n\n" +
                "Main points include: " + "\n".join(summary['Outline Summary']['Main Points']) + "\n\n" +
                "Key discoveries include: " + "\n".join(summary['Outline Summary']['Key Discoveries'])
            )

            # Accent selection
            accent_options = {
                "English (United States)": "us",
                "English (Nigeria)": "com.ng",
                "English (India)": "co.in",
                "English (Australia)": "com.au",
                "English (United Kingdom)": "co.uk"
            }
            accent = st.selectbox(
                "Select an accent:",
                options=list(accent_options.keys())
            )
            tld = accent_options[accent]
            
            # Button to generate speech
            if st.button("Generate Speech"):
                if full_summary_text_for_tts.strip():
                    try:
                        with st.spinner("Generating audio..."):
                            tts = gTTS(text=full_summary_text_for_tts, lang='en', tld=tld)
                            audio_bytes = BytesIO()
                            tts.write_to_fp(audio_bytes)
                            st.session_state.audio_data = audio_bytes.getvalue()
                        st.success("Done!")
                    except Exception as e:
                        st.error(f"Error generating speech: {e}")
                else:
                    st.warning("No text available to convert to speech.")

            # NEW: PDF Download Button using st.download_button
            # Placed directly below "Generate Speech" button within main_container
            # Only show if summary_output exists
            if 'summary_output' in st.session_state and st.session_state['summary_output'] is not None:
                pdf_bytes = generate_summary_pdf_bytes(st.session_state['summary_output'])
                st.download_button(
                    label="Download Summary (PDF)",
                    data=pdf_bytes,
                    file_name="SummaRead_Summary.pdf",
                    mime="application/pdf",
                    use_container_width=True,
                    help="Click to download the full summary as a PDF file."
                )

        else:
            # If no summary exists, tell the user to generate one
            st.write("<h3 style='text-align:center'>🗣️ Summary Reader</h3>", unsafe_allow_html=True)
            st.info("Please go to the 'Text Extraction' page to generate a summary first.")
            st.page_link("pages/2_source.py", label="Go to Text Extraction", icon="📝")

    # Fixed footer in the second container (for audio player)
    with footer_container:
        st.markdown(
            """
            <div class="fixed-footer">
                <h4></h4>
            </div>
            """,
            unsafe_allow_html=True
        )
        
        if 'audio_data' in st.session_state:
            audio_base64 = base64.b64encode(st.session_state.audio_data).decode('utf-8')
            st.markdown(
                f"""
                <div class="fixed-footer">
                    <audio controls autoplay style="width:100%">
                        <source src="data:audio/mp3;base64,{audio_base64}" type="audio/mp3">
                    </audio>
                </div>
                """,
                unsafe_allow_html=True
            )
else:
    # Content to show if the user is NOT logged in
    st.write("<h3 style='text-align:center'>🗣️ Summary Reader</h3>", unsafe_allow_html=True)
    st.info("Please log in to use the summary reader features.")
    st.page_link("0_profile.py", label="Go to Login/Register", icon="🔑", use_container_width=True)
