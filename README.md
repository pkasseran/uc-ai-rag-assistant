# Unity Catalog AI RAG Assistant

A smart chatbot that helps developers integrate Unity Catalog AI with frameworks like LangChain, LlamaIndex, and OpenAI. Ask questions in natural language and get accurate answers with source citations.

## ✨ Features

- 🤖 **Smart Q&A**: Ask questions like "What is a Unity Catalog Function?" or "How do I integrate LangChain?"
- 🔍 **Intelligent Search**: Handles synonyms (e.g., "UC Function" = "Unity Catalog Function")
- 👥 **Multi-User**: Authentication with persistent chat history
- 📚 **Source Citations**: All answers include links to official documentation
- ⚡ **Auto-Updated**: Automatically scrapes and processes Unity Catalog AI docs

## 🚀 Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Setup Environment
```bash
cp .env.example .env
# Add your OpenAI API key to .env
```

### 3. Initialize System (One-time)
```bash
# Scrape and process documents
cd code/document_scraping
./scrap_n_group.sh    # Linux/Mac
# or
scrap_n_group.bat     # Windows

# Build vector database
cd ..
python build_vector_store.py
```

### 4. Run the App
```bash
./run_streamlite.sh   # Linux/Mac
# or  
run_streamlite.bat    # Windows
```

Visit `http://localhost:8501` and start chatting! 🎉

## 💬 Example Questions

- "What is a Unity Catalog Function?"
- "How do I create a UC Function?"
- "Which AI frameworks integrate with Unity Catalog?"
- "Show me LangChain integration examples"

## 🛠️ Customization

### Add New Documentation Sources
Edit `config/uc_ai_scrap_config.yml`:
```yaml
urls:
  - "https://docs.unitycatalog.io/ai/"
  - "your-new-documentation-url"
```

### Add Synonyms
Edit `config/synonyms_config.yaml`:
```yaml
SYNONYMS:
  "Unity Catalog Function":
    - "UC Function"
    - "Your custom term"
```

## 📁 Project Structure
```
module1-rag-assistant/
├── code/                   # Main application code
├── config/                 # Configuration files
├── documents/              # Processed documents
├── vector_store/           # FAISS database
├── requirements.txt        # Python dependencies
└── README.md              # This file
```

## 🔧 Troubleshooting

**App won't start?**
```bash
python code/build_vector_store.py  # Rebuild database
```

**No answers to questions?**
```bash
cd code/document_scraping
./scrap_n_group.sh  # Re-scrape documents
```

**Authentication issues?**
```bash
rm database/chat_history.db  # Reset database
```

## 📚 Documentation

For detailed setup, architecture, and development guide, see [Installation_and_documentation.md](Installation_and_documentation.md)

## 🤝 Contributing

1. Fork the repository
2. Create your feature branch
3. Test your changes
4. Submit a pull request

---

**Need help?** Check the troubleshooting section or open an issue.

*Built with ❤️ using LangChain, Streamlit, and OpenAI*