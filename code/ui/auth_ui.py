import streamlit as st
from database.auth import AuthManager

class AuthUI:
    def __init__(self, auth_manager: AuthManager):
        self.auth_manager = auth_manager
    
    def show_login_page(self):
        """Display login/register page"""
        st.set_page_config(page_title="Unity Catalog AI - Login", layout="centered")
        
        st.title("🔐 Unity Catalog AI Assistant")
        st.subheader("Please login to continue")
        
        # Create tabs for Login and Register
        login_tab, register_tab = st.tabs(["Login", "Register"])
        
        with login_tab:
            self._show_login_form()
        
        with register_tab:
            self._show_register_form()
    
    def _show_login_form(self):
        with st.form("login_form"):
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            login_button = st.form_submit_button("Login")
            
            if login_button:
                if username and password:
                    user = self.auth_manager.authenticate_user(username, password)
                    if user:
                        st.session_state.authenticated = True
                        st.session_state.user_id = user[0]
                        st.session_state.username = user[1]
                        st.success("Login successful!")
                        st.rerun()
                    else:
                        st.error("Invalid username or password")
                else:
                    st.error("Please enter both username and password")
    
    def _show_register_form(self):
        with st.form("register_form"):
            new_username = st.text_input("Choose Username")
            new_password = st.text_input("Choose Password", type="password")
            confirm_password = st.text_input("Confirm Password", type="password")
            email = st.text_input("Email (optional)")
            register_button = st.form_submit_button("Register")
            
            if register_button:
                if new_username and new_password:
                    if new_password == confirm_password:
                        user_id = self.auth_manager.create_user(new_username, new_password, email)
                        if user_id:
                            st.success("Registration successful! Please login.")
                        else:
                            st.error("Username already exists or registration failed")
                    else:
                        st.error("Passwords do not match")
                else:
                    st.error("Please enter username and password")
    
    @staticmethod
    def logout():
        """Logout user and clear session state"""
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()
    
    @staticmethod
    def is_authenticated():
        """Check if user is authenticated"""
        return st.session_state.get("authenticated", False)