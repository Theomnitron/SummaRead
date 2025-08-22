# Fnl Prj
# SummaRead - welcome page
import streamlit as st
from auth_utils.firebase_manager import render_sidebar_profile # Import the common sidebar renderer
import time

st.set_page_config(
            page_title= 'SummaRead',
            layout= 'centered',
            menu_items={
                'Get Help': 'https://www.extremelycoolapp.com/help',
                'Report a bug': "https://www.extremelycoolapp.com/bug",
                'About': "# This is a header. This is an *extremely* cool app!"
            },
        )

# Call the common sidebar profile renderer at the very beginning
render_sidebar_profile()


# --- Main Page Content ---
# This content will only be shown if the user is logged in
# if st.session_state.get('logged_in', False):

st.markdown('<h6 style = "text-align: center; padding: 200px 0 0; font-family: Inter; font-size: 13px;">Welcome to</h6>', unsafe_allow_html= True)
st.markdown('<h2 style = "text-align: center; padding: 0; margin-top: -5px; font-weight: bold; font-size: 50px;">SummaRead!</h2>', unsafe_allow_html= True)


# The "Get Started" button to navigate to the source page
welcome_btn = st.button('Get Started', use_container_width=True)

if welcome_btn:
    if st.session_state.get('logged_in', True):
        st.switch_page('pages/2_Extract.py')
    else:
        st.switch_page('pages/1_Profile.py')
