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

# head = st.markdown('<h2>Heading</h2>', unsafe_allow_html= True)
# body = st.markdown("""
#                     <p>
#                         A short label explaining to the user what this button is for.
#                         The label can optionally contain GitHub-flavored Markdown of the following types: Bold, Italics, Strikethroughs, Inline Code, Links, and Images.
#                         Images display like icons, with a max height equal to the font height.
#                         Unsupported Markdown elements are unwrapped so only their children (text contents) render.
#                         Display unsupported elements as literal characters by backslash-escaping them. E.g., "1\. Not an ordered list".
#                         See the body parameter of st.markdown for additional, supported Markdown directives.
#                     </p>
#                     """, unsafe_allow_html= True)
# message = st.text_area("Message", value="Lorem ipsum.\nStreamlit is cool.")
# combo = head + body

# if st.button("Prepare download"):
#     st.download_button(
#         label="Download text",
#         data=combo,
#         file_name="combo.docx",
#         on_click="ignore",
#         type="primary",
#         icon=":material/download:",
#     )
