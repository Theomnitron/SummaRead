# import streamlit as st
# import base64
# from io import BytesIO
# from gtts import gTTS
# import time

# # ONLY ADDED: Import the common sidebar renderer from auth_utils
# from auth_utils.firebase_manager import render_sidebar_profile


# st.set_page_config(
#             page_title="SummaReader",
#             layout="centered"
#         )

# # ONLY ADDED: Call the common sidebar profile renderer at the very beginning of the script
# render_sidebar_profile()

# # Add the 'Open-Dyslexic' font and custom CSS (PRESERVED - NO CHANGES)
# st.markdown('''
# <style>
# @import url('https://fonts.googleapis.com/css2?family=Open+Dyslexic:wght@400;700&display=swap');

# /* Main Streamlit style overrides */
# .stMainMenu, .st-emotion-cache-weq6zh.em9zgd017 {
#     visibility: hidden;
# }
# /* Specific styling for summary components */
# .heading-summary {
#     font-family: 'Open-Dyslexic', sans-serif !important;
#     font-size: 28px !important;
#     font-weight: 700;
#     text-align: center;
#     text-transform: capitalize;

# }
# .body-summary {
#     font-family: 'Open-Dyslexic', sans-serif !important;
#     font-size: 15px !important;
#     line-height: 2rem;
#     letter-spacing: 0.5px;
#     padding: 0px 5px;
# }
# .points{
#     font-family: 'Open-Dyslexic', sans-serif !important;
#     font-size: 20px !important;
# }
# .outline-summary {
#     font-family: 'Open-Dyslexic', sans-serif !important;
#     font-size: 15px !important;
#     padding-left: 10px;
#     line-height: 2rem;
#     letter-spacing: 0.5px;
# }

# /* Footer styling */
# .fixed-footer {
#     position: fixed;
#     bottom: 0;
#     left: 0;
#     right: 0;
#     background: rgba(0, 0, 0, 0);
#     padding-left: 15px;
#     padding-right: 15px;
#     margin-bottom: 40px;
#     border-radius: 2rem;
#     box-shadow: 0 -2px 10px rgba(0, 0, 0, 0);
#     z-index: 1000;
# }
# </style>
# ''', unsafe_allow_html= True)


# # Main content container
# main_container = st.container()
# footer_container = st.container()


# with main_container:

#     # Check if the summary exists in session state (PRESERVED - NO CHANGES)
#     if 'summary_output' in st.session_state and st.session_state['summary_output'] is not None:
#         summary = st.session_state['summary_output']

#         # Display the heading with the biggest font-size and center alignment
#         st.markdown(f"<h2 class='heading-summary'>{summary['Heading']}</h2>", unsafe_allow_html=True)

#         st.write('---')

#         # Display the body summary with the custom font
#         st.markdown(f"<p class='body-summary'>{summary['Body Summary']}</p>", unsafe_allow_html=True)

#         st.write('---')

#         # Display the outline summary with bullet points and indentation
#         notes = 'Important Points:'
#         st.markdown(f'<h4 class= "points">{notes}</h4>', unsafe_allow_html= True)
#         # Main Points
#         for point in summary['Outline Summary']['Main Points']:
#             st.markdown(f'''
#                         <ul class='outline-summary'>
#                             <li>{point}</li>
#                         </ul>
#                         ''', unsafe_allow_html=True)

#         # Key Discoveries
#         for discovery in summary['Outline Summary']['Key Discoveries']:
#             st.markdown(f'''
#                         <ul class='outline-summary'>
#                             <li>{discovery}</li>
#                         </ul>
#                         ''', unsafe_allow_html=True)

#         # --- Construct the full summary text for TTS --- (PRESERVED - NO CHANGES)
#         # Combine Heading, Body Summary, and Outline points into a single string
#         # Use multiple newlines for clearer pauses in speech
#         full_summary_text_for_tts = (
#             summary['Heading'] + "\n\n" +
#             summary['Body Summary'] + "\n\n" + notes + "\n" + "\n".join(summary['Outline Summary']['Main Points']) + "\n\n" + "\n".join(summary['Outline Summary']['Key Discoveries'])
#         )
#         # Note: I've added "Main points include:" and "Key discoveries include:" for better speech flow.
#         # If you strictly want NO labels, even for speech, remove these parts.

#         # Accent selection (PRESERVED - NO CHANGES)
#         accent_options = {
#             "English (United States)": "us",
#             "English (Nigeria)": "com.ng",
#             "English (India)": "co.in",
#         }
#         accent = st.selectbox(
#             "Select an accent:",
#             options=list(accent_options.keys())
#         )
#         tld = accent_options[accent]
            
#         # Button to generate speech - now directly uses full_summary_text_for_tts (PRESERVED - NO CHANGES)
#         if st.button("Generate Speech"):
#             if full_summary_text_for_tts.strip():
#                 try:
#                     with st.spinner("Generating audio..."):
#                         # Pass the full_summary_text_for_tts directly to gTTS
#                         tts = gTTS(text=full_summary_text_for_tts, lang='en', tld=tld)
#                         audio_bytes = BytesIO()
#                         tts.write_to_fp(audio_bytes)
#                         st.session_state.audio_data = audio_bytes.getvalue()
#                     st.success("Done!")
#                 except Exception as e:
#                     st.error(f"Error generating speech: {e}")
#             else:
#                 st.warning("No text available to convert to speech.")
#     else:
#         # If no summary exists, tell the user to generate one (PRESERVED - NO CHANGES)
#         st.write("<h3 style='text-align:center; font-size: 32px; font-weight: bold;'>🔊SummaRead!</h3>", unsafe_allow_html=True)
#         st.info("Please go to the 'Text Extraction' page to generate a summary first.")
#         if st.button('Go to Text Extraction', icon="📝", use_container_width= True):
#             st.switch_page("pages/2_Extract.py")

# # Fixed footer in the second container (PRESERVED - NO CHANGES)
# with footer_container:
#     st.markdown(
#         """
#         <div class="fixed-footer">
#             <h4></h4>
#         </div>
#         """,
#         unsafe_allow_html=True
#     )
    
#     if 'audio_data' in st.session_state:
#         audio_base64 = base64.b64encode(st.session_state.audio_data).decode('utf-8')
#         st.markdown(
#             f"""
#             <div class="fixed-footer">
#                 <audio controls autoplay style="width:100%">
#                     <source src="data:audio/mp3;base64,{audio_base64}" type="audio/mp3">
#                 </audio>
#             </div>
#             """,
#             unsafe_allow_html=True
#         )

# import streamlit as st

# message = st.text_area("Message", value="Lorem ipsum.\nStreamlit is cool.")

# if st.button("Prepare download"):
#     st.download_button(
#         label="Download text",
#         data=message,
#         file_name="message.pdf",
#         on_click="ignore",
#         type="primary",
#         icon=":material/download:",
#     )

# import streamlit as st
# from pdf2docx import Converter
# import io

# st.write("hello world")

# uploaded_file = st.text_area('valuhi', value= "Hey there")
# if uploaded_file is not None:
#     # To read file as bytes:
#     bytes_data = uploaded_file.getvalue()
#     cv = Converter(stream=bytes_data)
#     out_stream = io.BytesIO()
#     cv.convert(out_stream)
#     cv.close()
#     # Download the file
#     btn = st.download_button(
#         label="Download image",
#         data=out_stream.getvalue(),
#         file_name="sample.docx",
#         mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
#     )


import streamlit as st
import streamlit.components.v1 as components

# Streamlit output goes here
st.title("Sales report")
st.write('---')
st.subheader("Sales report")
st.write('---')
st.write("srggwvw wvbwev weviw eviwe vweivwe vweivw evwevwviwev vwv")
# st.bar_chart(data)

show_print_button ="""
    <script>
        function print_page(obj) {
            obj.style.display = "none";
            parent.window.print();
        }
    </script>
    <button onclick="print_page(this)">
        Print page (choose 'Save as PDF' in print dialogue)
    </button>
    """
components.html(show_print_button)


