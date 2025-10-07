# frontend/views/auth_view.py
import streamlit as st
from backend.auth_service import register_user, authenticate_user

# ----------------------------
# AUTHENTICATION UI
# ----------------------------
def render_auth_view():
    st.title("📄 PDF Intelligence Platform")
    login_tab, register_tab = st.tabs(["Login", "Register"])

    # --- LOGIN TAB ---
    with login_tab:
        st.subheader("Sign in")
        uname = st.text_input("Username", key="login_username", label_visibility="visible")
        pwd = st.text_input("Password", type="password", key="login_password")
        if st.button("Login"):
            user = authenticate_user(uname, pwd)   # ✅ no strip(), take exact input
            if user:
                st.session_state.auth["logged_in"] = True
                st.session_state.auth["username"] = user.username
                st.session_state.auth["user_id"] = user.id

                # ✅ show username safely without markdown parsing issues
                st.success("Welcome back!")
                st.code(user.username)

                st.rerun()
            else:
                st.error("Invalid username or password.")

    # --- REGISTER TAB ---
    with register_tab:
        st.subheader("Create an account")
        r_uname = st.text_input("Choose username", key="reg_username", label_visibility="visible")
        r_pwd = st.text_input("Choose password", type="password", key="reg_password")
        r_pwd2 = st.text_input("Confirm password", type="password", key="reg_password2")

        if st.button("Register"):
            if not r_uname or not r_pwd:
                st.error("Enter username and password.")
            elif r_pwd != r_pwd2:
                st.error("Passwords do not match.")
            else:
                try:
                    # ✅ no strip(), preserve underscores exactly
                    user = register_user(r_uname, r_pwd)

                    st.success("Registered successfully! You can now log in as:")
                    st.code(user.username)

                except ValueError as ve:
                    st.error(str(ve))
                except Exception as e:
                    st.error(f"Registration failed: {e}")
