# Agentic RAG Assistant for Unity Catalog AI Integration

An advanced Retrieval-Augmented Generation (RAG) assistant specifically engineered to help developers navigate and integrate Unity Catalog AI with various supported frameworks including LangChain, LlamaIndex, OpenAI, and others.

## 🎯 Purpose

This system employs an intelligent document processing pipeline that automatically scrapes, processes, and indexes Unity Catalog OSS AI documentation into a sophisticated, searchable knowledge system. Developers can pose natural language questions and receive precise, citation-grounded answers with accompanying code examples and setup steps.

Key features:
- **Intelligent synonym handling** (e.g., "UC Function" vs "Unity Catalog Function")
- **Authentication-enabled web interface** with persistent chat history
- **Advanced document processing** with configurable web scraping
- **Multi-user support** suitable for team environments

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- OpenAI API key

### Installation

```bash
# Clone and navigate to project
cd module1-rag-assistant

# Install dependencies
pip install -r requirements.txt

# Configure environment variables
cp .env.example .env
# Edit .env with your OpenAI API key
```

### Initial Setup

```bash
# 1. Scrape and process documents (one-time setup)
cd code/document_scraping
python webdoc_scraper.py uc_ai_scrap_config.yml
python convert_to_RAG_ready_groups.py uc_ai_scrap_config.yml

# 2. Build vector store
cd ..
python build_vector_store.py

# 3. Run the application
./run_streamlite.sh    # Linux/Mac
# or
run_streamlite.bat     # Windows
```

## 🏗️ Architecture

### System Components

```
module1-rag-assistant/
├── code/
│   ├── database/           # User authentication & chat history
│   │   ├── auth.py
│   │   └── db_manager.py
│   ├── document_scraping/  # Document processing pipeline
│   │   ├── webdoc_scraper.py
│   │   └── convert_to_RAG_ready_groups.py
│   ├── rag/               # RAG system components
│   │   ├── components.py
│   │   └── utils.py
│   ├── ui/                # User interface
│   │   └── auth_ui.py
│   ├── config/            # Configuration management
│   │   └── config_loader.py
│   ├── build_vector_store.py
│   └── rag_assistant_ui.py
├── config/                # YAML configuration files
│   ├── prompt_config.yaml
│   ├── synonyms_config.yaml
│   └── config.yaml
├── documents/             # Processed documents
├── vector_store/          # FAISS vector index
└── database/             # SQLite database
```

### Document Processing Pipeline

1. **Web Scraping**: Configurable scraping using `WebDocumentScraper`
2. **Content Processing**: Intelligent HTML parsing with markdown link preservation
3. **Document Grouping**: Header-based chunking with section breadcrumbs
4. **Synonym Augmentation**: Automatic injection of terminology variations
5. **Vector Store Creation**: FAISS indexing with OpenAI embeddings

### RAG System Features

- **Advanced Retrieval**: FAISS-powered semantic search with synonym handling
- **Context-Aware Generation**: LangChain ConversationalRetrievalChain
- **Memory Management**: Conversation history with token-based summarization
- **Source Attribution**: All answers include citations and verification links

## ⚙️ Configuration

### Document Scraping Configuration

```yaml
# config/scraping_config.yaml
urls:
  - "https://docs.unitycatalog.io/ai/"
  - "https://docs.unitycatalog.io/ai/integrations/"
tags: ["h1", "h2", "h3", "h4", "p", "pre", "ul", "ol", "li"]
output_raw_file: "unity_catalog_docs.json"
output_rag_grouping_file: "unity_catalog_docs_grouped.json"
```

### Synonym Management

```yaml
# config/synonyms_config.yaml
SYNONYMS:
  "Unity Catalog Function":
    - "UC Function"
    - "UC function"
    - "Unity Catalog (UC) function"
    - "Unity Catalog Functions"
  "AI":
    - "GenAI"
    - "GenAI framework"
    - "Artificial Intelligence"
    - "Generative AI"
```

### Prompt Customization

```yaml
# config/prompt_config.yaml
ai_assistant_system_prompt:
  role: "You are an expert Unity Catalog AI assistant..."
  style_or_tone:
    - "Be precise and technical"
    - "Include code examples when relevant"
  output_constraints:
    - "Always cite sources"
    - "Acknowledge when information is unavailable"
```

## 💻 Usage Examples

### Basic Queries
- "What is a Unity Catalog Function?"
- "How do I integrate LangChain with Unity Catalog AI?"
- "Show me examples of UC Function implementation"

### Advanced Features
- **Multi-turn conversations** with context retention
- **Source verification** via embedded documentation links  
- **Synonym-aware search** handles terminology variations
- **Section-aware chunking** preserves document hierarchy

## 🛠️ Development

### Key Classes

#### `WebDocumentScraper`
```python
from document_scraping.webdoc_scraper import WebDocumentScraper

scraper = WebDocumentScraper(log_level="INFO")
data = scraper.scrape_urls(
    urls=["https://docs.unitycatalog.io/ai/"],
    tags=["h1", "h2", "p", "pre"],
    output_file="scraped_docs.json"
)
```

#### `VectorStoreBuilder`
```python
from build_vector_store import VectorStoreBuilder

builder = VectorStoreBuilder(ROOT_DIR, "docs.json")
builder.build_vector_store(
    augment_synonyms=True,
    inject_syn_chunks=False
)
```

#### `RAGAssistantUI`
```python
from rag_assistant_ui import RAGAssistantUI

ui = RAGAssistantUI(ROOT_DIR)
ui.run()
```

### Extending the System

#### Add New Document Sources
1. Update `config/scraping_config.yaml` with new URLs
2. Run the scraping pipeline
3. Rebuild the vector store

#### Customize Response Format
1. Modify `config/prompt_config.yaml`
2. Update `rag/utils.py` formatting functions
3. Restart the application

#### Add New Synonyms
1. Update `config/synonyms_config.yaml`
2. Rebuild vector store to incorporate changes

## 🔧 Troubleshooting

### Common Issues

**Vector store not found**
```bash
# Rebuild the vector store
python code/build_vector_store.py
```

**Authentication issues**
```bash
# Check database permissions
ls -la database/
# Recreate database if needed
rm database/chat_history.db
```

**Scraping failures**
- Verify internet connectivity to target URLs
- Check if website structure has changed
- Review scraping configuration in YAML files

## 📊 Performance & Quality

### Technical Specifications
- **Retrieval Accuracy**: Enhanced through synonym augmentation
- **Response Quality**: Chain-of-thought prompting with source grounding
- **Scalability**: Modular architecture supports multiple document sources
- **Reliability**: Comprehensive error handling and logging

### Quality Assurance
- All responses include source citations
- Document processing preserves formatting and code blocks
- Multi-level validation ensures data quality
- Deduplication prevents redundant information

## 🤝 Contributing

This system is designed for enterprise adoption with:
- **Modular architecture** for easy extension
- **Comprehensive documentation** 
- **Configuration-driven customization**
- **Production-ready deployment** options

## 📄 License

[Add your license information here]

---

*This system represents a significant advancement in AI-powered developer tooling, combining state-of-the-art RAG techniques with production-ready software engineering practices.*