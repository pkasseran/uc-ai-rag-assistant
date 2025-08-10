import os
import streamlit as st
from dotenv import load_dotenv
from langchain_community.vectorstores import FAISS
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain.prompts import PromptTemplate
from config.config_loader import ConfigLoader

class RAGComponents:
    def __init__(self, root_dir: str):
        self.root_dir = root_dir
        self.config_loader = ConfigLoader(root_dir)
        self.vector_store_path = os.path.join(root_dir, "vector_store", "faiss_index_json_ossuc_ai")
    
    @st.cache_resource
    def load_components(_self):
        """Load RAG components (cached)"""
        load_dotenv()
        openai_api_key = os.getenv("OPENAI_API_KEY")
        
        # Load configurations
        config = _self.config_loader.get_config()
        prompt_config = _self.config_loader.get_prompt_config()
        
        reasoning_strategy = config["reasoning_strategies"]["CoT"]
        llm_model = config["llm"]
        prompt_config_val = prompt_config["ai_assistant_system_prompt_advanced"]
        
        # Load FAISS vectorstore
        embeddings = OpenAIEmbeddings(api_key=openai_api_key)
        vectorstore = FAISS.load_local(
            _self.vector_store_path,
            embeddings=embeddings,
            allow_dangerous_deserialization=True
        )
        
        # Create retriever
        retriever = vectorstore.as_retriever(
            search_type="mmr",
            search_kwargs={"k": 8, "fetch_k": 25}
        )
        
        # Build prompt
        rag_prompt = PromptTemplate.from_template(
            _self.config_loader.build_rag_prompt(prompt_config_val, reasoning_strategy)
        )
        
        # Load LLM
        llm = ChatOpenAI(
            model=llm_model,
            temperature=0,
            api_key=openai_api_key
        )
        
        return llm, retriever, rag_prompt