import os
import logging
import streamlit as st
from datetime import datetime
from langchain.memory import ConversationSummaryBufferMemory
from langchain.schema import HumanMessage, AIMessage
from langchain.chains import ConversationalRetrievalChain

from database.db_manager import DatabaseManager
from database.auth import AuthManager
from rag.components import RAGComponents
from rag.utils import format_answer, deduplicate_docs
from ui.auth_ui import AuthUI

class RAGAssistantUI:
    def __init__(self, root_dir):
        self.root_dir = root_dir
        self.setup_logging()
        
        # Initialize components with logging
        self.logger.info("Initializing RAG Assistant UI components...")
        try:
            self.db_manager = DatabaseManager(root_dir)
            self.auth_manager = AuthManager(self.db_manager.db_path)
            self.rag_components = RAGComponents(root_dir)
            self.auth_ui = AuthUI(self.auth_manager)
            self.logger.info("All components initialized successfully")
        except Exception as e:
            self.logger.error(f"Failed to initialize components: {e}")
            raise

    def setup_logging(self):
        """Setup logging configuration for the UI"""
        logs_dir = os.path.join(self.root_dir, "logs")
        os.makedirs(logs_dir, exist_ok=True)
        
        log_file = os.path.join(logs_dir, f"rag_ui_{datetime.now().strftime('%Y%m%d')}.log")
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler()  # Console output
            ]
        )
        
        self.logger = logging.getLogger(__name__)
        self.logger.info("Logging initialized")

    def setup_page(self):
        """Setup Streamlit page configuration"""
        self.logger.info("Setting up Streamlit page configuration")
        st.set_page_config(page_title="Unity Catalog AI - RAG QA", layout="wide")

    def show_header(self):
        """Display application header"""
        username = st.session_state.get('username', 'Unknown')
        self.logger.debug(f"Displaying header for user: {username}")
        
        col1, col2 = st.columns([4, 1])
        with col1:
            st.title("🧠 Unity Catalog AI - Assistant")
            st.caption(f"Welcome {username}! Ask anything about Unity Catalog AI documents")
        with col2:
            if st.button("🚪 Logout"):
                self.logger.info(f"User {username} logging out")
                self.auth_ui.logout()

    def get_current_user_id(self):
        """Get current user ID from session state"""
        user_id = st.session_state.get('user_id')
        self.logger.debug(f"Retrieved user_id: {user_id}")
        return user_id

    def get_user_chat_history(self, user_id):
        """Retrieve user's chat history"""
        key = f"chat_history_{user_id}"
        if key not in st.session_state:
            self.logger.info(f"Loading chat history for user_id: {user_id}")
            try:
                st.session_state[key] = self.db_manager.load_chat_history(user_id)
                history_count = len(st.session_state[key])
                self.logger.info(f"Loaded {history_count} messages from chat history for user {user_id}")
            except Exception as e:
                self.logger.error(f"Failed to load chat history for user {user_id}: {e}")
                st.session_state[key] = []
        return st.session_state[key]

    def get_user_memory(self, user_id, llm, user_chat_history):
        """Initialize or retrieve user's conversation memory"""
        key = f"memory_{user_id}"
        if key not in st.session_state:
            self.logger.info(f"Initializing conversation memory for user_id: {user_id}")
            try:
                memory = ConversationSummaryBufferMemory(
                    llm=llm,
                    max_token_limit=1000,
                    memory_key="chat_history",
                    return_messages=True,
                    output_key="answer",
                )
                
                # Restore chat history to memory
                message_count = 0
                for msg in user_chat_history:
                    if isinstance(msg, HumanMessage):
                        memory.chat_memory.add_user_message(msg.content)
                    else:
                        memory.chat_memory.add_ai_message(msg.content)
                    message_count += 1
                
                st.session_state[key] = memory
                self.logger.info(f"Initialized memory with {message_count} messages for user {user_id}")
            except Exception as e:
                self.logger.error(f"Failed to initialize memory for user {user_id}: {e}")
                raise
        return st.session_state[key]

    def build_conv_chain(self, llm, retriever, memory, rag_prompt):
        """Build conversational retrieval chain"""
        self.logger.info("Building conversational retrieval chain")
        try:
            chain = ConversationalRetrievalChain.from_llm(
                llm=llm,
                retriever=retriever,
                memory=memory,
                combine_docs_chain_kwargs={"prompt": rag_prompt},
                return_source_documents=True
            )
            self.logger.info("Conversational chain built successfully")
            return chain
        except Exception as e:
            self.logger.error(f"Failed to build conversational chain: {e}")
            raise

    def display_chat_history(self, user_chat_history):
        """Display chat history in the UI"""
        message_count = len(user_chat_history)
        self.logger.debug(f"Displaying {message_count} messages from chat history")
        
        for i, msg in enumerate(user_chat_history):
            role = "user" if isinstance(msg, HumanMessage) else "assistant"
            with st.chat_message(role):
                st.markdown(msg.content)

    def handle_user_query(self, conv_chain, user_chat_history, current_user_id):
        """Handle user query and generate response"""
        user_query = st.chat_input("Ask your question here...")
        if user_query:
            self.logger.info(f"Processing query from user {current_user_id}: {user_query[:100]}...")
            
            # Add user message to history
            user_chat_history.append(HumanMessage(content=user_query))
            st.session_state[f"chat_history_{current_user_id}"] = user_chat_history
            
            with st.chat_message("user"):
                st.markdown(user_query)
            
            # Save user message to database
            try:
                self.db_manager.save_message(current_user_id, "human", user_query)
                self.logger.debug(f"Saved user message to database for user {current_user_id}")
            except Exception as e:
                self.logger.error(f"Failed to save user message: {e}")
            
            # Generate response
            with st.spinner("Thinking..."):
                try:
                    start_time = datetime.now()
                    result = conv_chain.invoke({"question": user_query})
                    response_time = (datetime.now() - start_time).total_seconds()
                    
                    response = result["answer"]
                    source_count = len(result.get("source_documents", []))
                    
                    self.logger.info(f"Generated response in {response_time:.2f}s with {source_count} sources")
                    self.logger.debug(f"Response preview: {response[:100]}...")
                    
                except Exception as e:
                    self.logger.error(f"Failed to generate response: {e}")
                    st.error("Sorry, I encountered an error while processing your question.")
                    return
            
            # Add AI response to history
            user_chat_history.append(AIMessage(content=response))
            st.session_state[f"chat_history_{current_user_id}"] = user_chat_history
            
            # Save AI response to database
            try:
                self.db_manager.save_message(current_user_id, "ai", response)
                self.logger.debug(f"Saved AI response to database for user {current_user_id}")
            except Exception as e:
                self.logger.error(f"Failed to save AI response: {e}")
            
            # Display response
            with st.chat_message("assistant"):
                st.markdown(format_answer(response))
            
            # Display sources
            self.display_sources(result.get("source_documents", []))

    def display_sources(self, source_documents):
        """Display source documents in expandable section"""
        sources = deduplicate_docs(source_documents)
        source_count = len(sources)
        self.logger.debug(f"Displaying {source_count} source documents")
        
        with st.expander("📚 Top 3 Source Documents"):
            for i, doc in enumerate(sources[:3]):
                title = doc.metadata.get("title", "Untitled")
                url = doc.metadata.get("source_url", "#")
                snippet = doc.page_content[:300].strip().replace("\n", " ")
                
                self.logger.debug(f"Source {i+1}: {title}")
                
                st.markdown(f"**Source {i+1}: {title}**")
                st.markdown(f"{snippet}...")
                st.markdown(f"[📎 Link to Source]({url})")

    def show_sidebar(self, current_user_id):
        """Display sidebar with user controls"""
        username = st.session_state.get('username', 'Unknown')
        
        with st.sidebar:
            st.header("Chat Controls")
            st.write(f"**User:** {username}")
            
            if st.button("🗑️ Clear My Chat History"):
                self.logger.info(f"Clearing chat history for user {current_user_id}")
                try:
                    self.db_manager.clear_chat_history(current_user_id)
                    st.session_state[f"chat_history_{current_user_id}"] = []
                    
                    # Clear memory if it exists
                    memory_key = f"memory_{current_user_id}"
                    if memory_key in st.session_state:
                        st.session_state[memory_key].clear()
                    
                    self.logger.info(f"Successfully cleared chat history for user {current_user_id}")
                    st.rerun()
                except Exception as e:
                    self.logger.error(f"Failed to clear chat history for user {current_user_id}: {e}")
                    st.error("Failed to clear chat history. Please try again.")

    def run(self):
        """Main application entry point"""
        self.logger.info("Starting RAG Assistant UI application")
        
        # Check authentication
        if not self.auth_ui.is_authenticated():
            self.logger.info("User not authenticated, showing login page")
            self.auth_ui.show_login_page()
            return

        try:
            # Setup UI components
            self.setup_page()
            self.show_header()
            
            # Get user information
            current_user_id = self.get_current_user_id()
            username = st.session_state.get('username', 'Unknown')
            self.logger.info(f"Authenticated user {username} (ID: {current_user_id}) accessing application")
            
            # Initialize RAG components
            user_chat_history = self.get_user_chat_history(current_user_id)
            llm, retriever, rag_prompt = self.rag_components.load_components()
            memory = self.get_user_memory(current_user_id, llm, user_chat_history)
            conv_chain = self.build_conv_chain(llm, retriever, memory, rag_prompt)
            
            # Display UI components
            self.display_chat_history(user_chat_history)
            self.handle_user_query(conv_chain, user_chat_history, current_user_id)
            self.show_sidebar(current_user_id)
            
        except Exception as e:
            self.logger.error(f"Critical error in main application loop: {e}")
            st.error("An unexpected error occurred. Please refresh the page and try again.")
            raise

if __name__ == "__main__":
    ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    ui = RAGAssistantUI(ROOT_DIR)
    ui.run()