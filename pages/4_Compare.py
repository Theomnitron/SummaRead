import streamlit as st

# ONLY ADDED: Import the common sidebar renderer from auth_utils
from auth_utils.firebase_manager import render_sidebar_profile

# --- Streamlit Configuration ---
st.set_page_config(
            page_title= 'Compare',
            layout="wide"
        )

# ONLY ADDED: Call the common sidebar profile renderer at the very beginning of the script
render_sidebar_profile()

# Removing Streamlit's Tripple dot (using markdown) (PRESERVED - NO CHANGES)
st.markdown('''
<style>

# Copy the class name of the buttons and style them to 'visibility: hidden;'
.stMainMenu.st-emotion-cache-czk5ss.e8lvnlb8{
visibility: hidden;
}

.st-emotion-cache-weq6zh.em9zgd017{
visibility: hidden;
}

</style>
''', unsafe_allow_html= True)




st.write("<h3 style='text-align:center; font-size: 32px; font-weight: bold;'>⚖️Comparison</h3>", unsafe_allow_html=True)

st.write('---')

# Comparison UI (PRESERVED - NO CHANGES)
col1, col2 = st.columns(2)

with col1:
    st.text_area(label= 'Original Text',
                    value= st.session_state.get('extracted_text', 'No original text available. Please extract text first.'),
                height= 500)

with col2:
    # Check if summary_output exists and is not None before trying to access its parts
    summary_output = st.session_state.get('summary_output', None)
    if summary_output:
    #         # Construct the summary string to display in the text area
    #     display_summary_text = (
    #         f"Heading: {summary_output.get('Heading', 'N/A')}\n\n"
    #         f"Body Summary:\n{summary_output.get('Body Summary', 'N/A')}\n\n"
    #         f"Main Points:\n" + "\n".join(summary_output.get('Outline Summary', {}).get('Main Points', ['NA'])) + "\n\n"
    #         f"Key Discoveries:\n" + "\n".join(summary_output.get('Outline Summary', {}).get('Key Discoveries', ['N/A']))
    #     )
        display_summary_text = (summary_output['Heading'] + "\n\n" + summary_output['Body Summary'] + "\n\n" + "Important Notes" + "\n" + "\n".join(summary_output['Outline Summary']['Main Points']) + "\n\n" + "\n".join(summary_output['Outline Summary']['Key Discoveries']))

    else:
        display_summary_text = "No summary available. Please generate a summary first."

    st.text_area(label= 'Summary',
                value= display_summary_text,
                height= 500)



