# pages/1_Profile.py
import streamlit as st
import time
from auth_utils.firebase_manager import (
    register_user,
    login_user,
    logout_user,
    render_sidebar_profile,
)


st.set_page_config(
            page_title='Register/Login',
            layout='centered'
        )


# Render sidebar profile (reads session_state)
render_sidebar_profile()

if "page" not in st.session_state:
    st.session_state.page = "Register"


# --- SWITCH FROM RADIO TO TABS ---
with st.container():
    tab_register, tab_login = st.tabs(["Register", "Login"])

if st.session_state.get("logged_in", False):
    st.success("You are already logged in!")
    upload = st.button("Let's SummaRead!")
    if upload:
        try:
            st.switch_page("pages/2_Extract.py")
        except Exception:
            st.rerun()

else:
    with tab_register:
        st.markdown('<h2 style="text-align: center; font-size: 20px; font-family: Inter; font-weight: bold;">Create an Account</h2>', unsafe_allow_html=True)
        with st.form("reg_form", clear_on_submit=False):
            col1, col2 = st.columns(2)
            first_name = col1.text_input("First Name", key="reg_fname")
            last_name = col2.text_input("Last Name", key="reg_lname")
            username = st.text_input("Username", key="reg_uname")
            email = st.text_input("Email Address", key="reg_email")
            password = st.text_input("Password", type="password", key="reg_pword")
            confirm_password = st.text_input("Confirm Password", type="password", key="reg_cp")

            _, col_btn, _ = st.columns(3)
            submit_btn = col_btn.form_submit_button("Register", use_container_width=True)

            if submit_btn:
                if not all([first_name, last_name, username, email, password, confirm_password]):
                    st.warning("Please fill all fields")
                elif password != confirm_password:
                    st.error("Passwords do not match!")
                elif len(password) < 6:
                    st.error("Password must be at least 6 characters")
                else:
                    with st.spinner("Creating your account..."):
                        result = register_user(email=email, password=password, display_name=f"{first_name}")

                    if result["success"]:
                        st.success("Registration successful! Please login.")
                        st.session_state.page = "Login"
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error(result["message"])


    with tab_login:
        st.markdown('<h2 style="text-align: center; font-size: 20px; font-family: Inter; font-weight: bold;">Login to Your Account</h2>', unsafe_allow_html=True)
        with st.form("login_form", clear_on_submit=False):
            email = st.text_input("Email Address", key="login_email")
            password = st.text_input("Password", type="password", key="login_pword")

            _, col_btn, _ = st.columns(3)
            submit_btn = col_btn.form_submit_button("Login", use_container_width=True)

            if submit_btn:
                if not email or not password:
                    st.warning("Please enter both email and password")
                else:
                    with st.spinner("Authenticating..."):
                        result = login_user(email=email, password=password)

                    if result["success"]:
                        st.success("Login successful!")
                        time.sleep(1)
                        try:
                            st.switch_page("Welcome.py")
                        except Exception:
                            st.rerun()
                    else:
                        st.error(result["message"])

        st.markdown(
            """
            <div style="text-align: center; margin-top: 20px;">
                <a href="#" style="text-decoration: none;">Forgot password?</a>
            </div>
            """,
            unsafe_allow_html=True,
        )

