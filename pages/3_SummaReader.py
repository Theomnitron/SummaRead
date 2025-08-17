import streamlit as st
import base64
from io import BytesIO
from gtts import gTTS
import time
from fpdf import FPDF # NEW: Import for PDF generation

# ONLY ADDED: Import the common sidebar renderer from auth_utils
from auth_utils.firebase_manager import render_sidebar_profile

st.set_page_config(layout="centered",
                page_title="SummaRead")

# ONLY ADDED: Call the common sidebar profile renderer at the very beginning of the script
render_sidebar_profile()

# Add the 'Open-Dyslexic' font and custom CSS (PRESERVED - NO CHANGES)
st.markdown('''
<style>
@import url('https://fonts.googleapis.com/css2?family=Open+Dyslexic:wght@400;700&display=swap');

/* Main Streamlit style overrides */
.stMainMenu, .st-emotion-cache-weq6zh.em9zgd017 {
    visibility: hidden;
}
/* Specific styling for summary components */
.heading-summary {
    font-family: 'Open-Dyslexic', sans-serif !important;
    font-size: 28px !important;
    font-weight: 700;
    text-align: center;
    text-transform: capitalize;

}
.body-summary {
    font-family: 'Open-Dyslexic', sans-serif !important;
    font-size: 14px !important;
    line-height: 2rem;
    letter-spacing: 0.5px;
    padding: 0px 5px;
}
.points{
    font-family: 'Open-Dyslexic', sans-serif !important;
    font-size: 20px !important;
}
.outline-summary {
    font-family: 'Open-Dyslexic', sans-serif !important;
    font-size: 14px !important;
    padding-left: 10px;
    line-height: 2rem;
    letter-spacing: 0.5px;
}

/* Fixed footer */
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
/* NEW: CSS for the floating download button container */
.floating-download-button-container {
    position: fixed;
    bottom: 20px; /* Adjust as needed to be below audio player */
    left: 50%;
    transform: translateX(-50%);
    z-index: 1001; /* Above the audio player footer */
    width: fit-content; /* Make it fit its content */
    display: flex; /* Use flexbox to center the button */
    justify-content: center;
    align-items: center;
}
/* NEW: Style for the actual download button inside the floating container */
.floating-download-button {
    background: linear-gradient(to right, #2196F3, #0D47A1); /* Consistent blue gradient */
    color: white;
    padding: 10px 20px;
    border: none;
    border-radius: 12px;
    font-weight: bold;
    cursor: pointer;
    box-shadow: 2px 2px 5px rgba(0,0,0,0.3);
    transition: all 0.3s ease;
    text-transform: uppercase;
    letter-spacing: 1px;
}
.floating-download-button:hover {
    background: linear-gradient(to right, #0D47A1, #2196F3);
    box-shadow: 4px 4px 10px rgba(0,0,0,0.5);
    transform: translateY(-2px);
}
.floating-download-button:active {
    background: #0A3D62;
    transform: translateY(0);
    box-shadow: inset 1px 1px 3px rgba(0,0,0,0.5);
}
</style>
''', unsafe_allow_html= True)


# --- PDF Generation Function (NEW) ---
@st.cache_data # Cache the PDF generation for the given summary data
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


with main_container:
        
    # Check if the summary exists in session state (PRESERVED - NO CHANGES)
    if 'summary_output' in st.session_state and st.session_state['summary_output'] is not None:
        summary = st.session_state['summary_output']

        # Display the heading with the biggest font-size and center alignment
        st.markdown(f"<h2 class='heading-summary'>{summary['Heading']}</h2>", unsafe_allow_html=True)

        st.write('---')

        # Display the body summary with the custom font
        st.markdown(f"<p class='body-summary'>{summary['Body Summary']}</p>", unsafe_allow_html=True)

        st.write('---')

        # Display the outline summary with bullet points and indentation
        notes = 'Important Points:'
        st.markdown(f'<h4 class= "points">{notes}</h4>', unsafe_allow_html= True)
        # Main Points
        for point in summary['Outline Summary']['Main Points']:
            st.markdown(f'''
                        <ul class='outline-summary'>
                            <li>{point}</li>
                        </ul>
                        ''', unsafe_allow_html=True)

        # Key Discoveries
        for discovery in summary['Outline Summary']['Key Discoveries']:
            st.markdown(f'''
                        <ul class='outline-summary'>
                            <li>{discovery}</li>
                        </ul>
                        ''', unsafe_allow_html=True)

        # --- Construct the full summary text for TTS --- (PRESERVED - NO CHANGES)
        # Combine Heading, Body Summary, and Outline points into a single string
        # Use multiple newlines for clearer pauses in speech
        full_summary_text_for_tts = (
            summary['Heading'] + "\n\n" +
            summary['Body Summary'] + "\n\n" + notes + "\n" + "\n".join(summary['Outline Summary']['Main Points']) + "\n\n" + "\n".join(summary['Outline Summary']['Key Discoveries'])
        )

        # Accent selection (PRESERVED - NO CHANGES)
        accent_options = {
            "English (United States)": "us",
            "English (Nigeria)": "com.ng",
            "English (India)": "co.in",
        }
        accent = st.selectbox(
            "Select an accent:",
            options=list(accent_options.keys())
        )
        tld = accent_options[accent]
            
        # Button to generate speech - now directly uses full_summary_text_for_tts (PRESERVED - NO CHANGES)
        if st.button("Generate Speech"):
            if full_summary_text_for_tts.strip():
                try:
                    with st.spinner("Generating audio..."):
                        # Pass the full_summary_text_for_tts directly to gTTS
                        tts = gTTS(text=full_summary_text_for_tts, lang='en', tld=tld)
                        audio_bytes = BytesIO()
                        tts.write_to_fp(audio_bytes)
                        st.session_state.audio_data = audio_bytes.getvalue()
                    st.success("Done!")
                except Exception as e:
                    st.error(f"Error generating speech: {e}")
            else:
                st.warning("No text available to convert to speech.")
    else:
        # If no summary exists, tell the user to generate one (PRESERVED - NO CHANGES)
        st.write("<h3 style='text-align:center'>🔊 SummaRead!</h3>", unsafe_allow_html=True)
        st.info("Please go to the 'Text Extraction' page to generate a summary first.")
        if st.button('Go to Text Extraction', icon="📝", use_container_width= True):
            st.switch_page("pages/2_source.py")

# Fixed footer in the second container (PRESERVED - NO CHANGES)
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
        # NEW: PDF Download Button (JavaScript)
        # Only show the download button if summary_output exists to ensure data is available
        if 'summary_output' in st.session_state and st.session_state['summary_output'] is not None:
            # Generate PDF bytes and Base64 encode them
            pdf_bytes = generate_summary_pdf_bytes(st.session_state['summary_output'])
            pdf_base64 = base64.b64encode(pdf_bytes).decode('utf-8')
            
            # Use st.markdown to inject the HTML button and JavaScript
            st.markdown(
                f"""
                <div class="floating-download-button-container">
                    <button class="floating-download-button" onclick="downloadPdf()">
                        Download Summary (PDF)
                    </button>
                </div>
                <script>
                    function downloadPdf() {{
                        const pdfBase64 = '{pdf_base64}';
                        const filename = 'SummaRead_Summary.pdf';
                        
                        const byteCharacters = atob(pdfBase64);
                        const byteNumbers = new Array(byteCharacters.length);
                        for (let i = 0; i < byteCharacters.length; i++) {{
                            byteNumbers[i] = byteCharacters.charCodeAt(i);
                        }}
                        const byteArray = new Uint8Array(byteNumbers);
                        const blob = new Blob([byteArray], {{ type: 'application/pdf' }});
                        
                        const link = document.createElement('a');
                        link.href = URL.createObjectURL(blob);
                        link.download = filename;
                        document.body.appendChild(link); // Append to body to make it clickable
                        link.click();
                        document.body.removeChild(link); // Clean up after click
                        URL.revokeObjectURL(link.href); // Release object URL
                    }}
                </script>
                """,
                unsafe_allow_html=True
            )
