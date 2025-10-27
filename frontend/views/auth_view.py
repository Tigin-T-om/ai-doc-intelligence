# frontend/views/auth_view.py
import streamlit as st
from backend.auth_service import register_user, authenticate_user
import time # Import time here

def render_auth_view():
    st.title("📄 PDF Intelligence Platform")
    st.markdown("---") # Add a divider

    # --- Centered Card Layout ---
    col1, col_main, col3 = st.columns([1, 2, 1]) # Adjust ratios as needed, e.g., [1,1.5,1]

    with col_main: # Place content in the middle column
        with st.container(border=True): # Create the card effect
            login_tab, register_tab = st.tabs(["Login", "Register"])

            # --- LOGIN TAB ---
            with login_tab:
                st.subheader("Sign in")
                uname = st.text_input("Username", key="login_username", label_visibility="visible")
                pwd = st.text_input("Password", type="password", key="login_password")
                
                # Center the login button
                login_col1, login_col_btn, login_col3 = st.columns([1,1,1])
                with login_col_btn:
                    if st.button("Login", use_container_width=True, type="primary"):
                        user = authenticate_user(uname, pwd)
                        if user:
                            st.session_state.auth["logged_in"] = True
                            st.session_state.auth["username"] = user.username
                            st.session_state.auth["user_id"] = user.id
                            st.session_state.auth["role"] = user.role
                            
                            st.success("Welcome back!")
                            st.code(user.username)
                            
                            time.sleep(1) # Short delay
                            st.rerun()
                        else:
                            st.error("Invalid username or password.")

            # --- REGISTER TAB ---
            with register_tab:
                st.subheader("Create an account")
                
                # Add New Fields
                col_fname, col_lname = st.columns(2)
                with col_fname:
                    r_fname = st.text_input("First Name", key="reg_fname")
                with col_lname:
                    r_lname = st.text_input("Last Name", key="reg_lname")
                
                r_email = st.text_input("Email Address", key="reg_email")
                r_uname = st.text_input("Choose username", key="reg_username")
                r_pwd = st.text_input("Choose password", type="password", key="reg_password")
                r_pwd2 = st.text_input("Confirm password", type="password", key="reg_password2")

                # Center the register button
                reg_col1, reg_col_btn, reg_col3 = st.columns([1,1,1])
                with reg_col_btn:
                     if st.button("Register", use_container_width=True, type="primary"):
                        # Basic validation for new fields
                        if not all([r_fname, r_lname, r_email, r_uname, r_pwd, r_pwd2]):
                            st.error("Please fill in all fields.")
                        elif r_pwd != r_pwd2:
                            st.error("Passwords do not match.")
                        # Add email format validation if desired (using regex or a library)
                        # elif not is_valid_email(r_email):
                        #     st.error("Please enter a valid email address.")
                        else:
                            try:
                                # --- IMPORTANT: Update register_user call ---
                                # This will fail until you update the backend function
                                user = register_user(
                                    username=r_uname,
                                    password=r_pwd,
                                    first_name=r_fname,
                                    last_name=r_lname,
                                    email=r_email
                                )
                                # --------------------------------------------
                                st.success("Registered successfully! You can now log in as:")
                                st.code(user.username)
                            except ValueError as ve: # Catch specific errors like "username exists"
                                st.error(str(ve))
                            except Exception as e: # Catch other potential errors
                                st.error(f"Registration failed: {e}")

    # Add some space below the card if needed
    st.markdown("")
    st.markdown("")