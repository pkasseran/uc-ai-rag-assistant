import os
import json
import yaml
from dotenv import load_dotenv

from langchain_core.documents import Document
from langchain.text_splitter import MarkdownHeaderTextSplitter, RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS

class VectorStoreBuilder:    
    def __init__(self, root_dir, document_filename, synonyms_config="synonyms_config.yaml"):

        self.root_dir = root_dir
        self.vector_store_path = os.path.join(root_dir, "vector_store", "faiss_index_json_ossuc_ai")
        self.document_dir = os.path.join(root_dir, "documents")
        self.config_dir = os.path.join(root_dir, "config")
        self.document_filename = document_filename

        # Load synonyms config
        with open(os.path.join(self.config_dir, synonyms_config), "r") as file:
            config = yaml.safe_load(file)
        self.synonyms = config['SYNONYMS']
        print("Loaded synonyms:", self.synonyms)

        # Load environment variables
        load_dotenv()
        self.openai_api_key = os.getenv("OPENAI_API_KEY")

    def inject_synonym_chunks(self, data):
        """
        Inject synthetic chunks containing synonym information at the beginning of the data.
        
        This method creates synthetic document chunks that explicitly list synonyms for canonical terms,
        helping improve retrieval by making synonym relationships explicit in the vector store.
        
        Args:
            data (list): List of document dictionaries to augment with synonym chunks
            
        Returns:
            list: The data list with synonym chunks inserted at the beginning
        """
        for canonical, synonyms in self.synonyms.items():
            chunk = {
                "source": "synthetic",
                "title": f"Synonyms for {canonical}",
                "content": f"{canonical} can also be referred to as: {', '.join(synonyms)}"
            }
            data.insert(0, chunk)
        return data

    def augment_chunks_with_synonyms(self, data):
        """
        Augment existing document chunks by appending synonym information to their content.
        
        This method scans through each document and if it contains terms that have synonyms,
        it appends a list of all synonyms (including plurals) to the document content.
        This helps with retrieval by making related terms more discoverable.
        
        Args:
            data (list): List of document dictionaries to augment with synonym information
            
        Returns:
            list: The data list with documents augmented with synonym information
        """
        for entry in data:
            title = entry.get("title", "").lower()
            content = entry.get("content", "").lower()
            for canonical, synonyms in self.synonyms.items():
                # Check all variants: canonical, plural, and synonyms
                variants = [canonical, canonical + "s"] + synonyms + [s + "s" for s in synonyms]
                if any(variant.lower() in title or variant.lower() in content for variant in variants):
                    all_syns = set([canonical] + synonyms + [canonical + "s"] + [s + "s" for s in synonyms])
                    entry["content"] += f"\n\n(Synonyms: {', '.join(all_syns)})"
        return data

    def inject_synthetic_chunk(self, data):
        integration_titles = [
            entry["title"].replace("¶", "").strip()
            for entry in data
            if "ai/integrations" in entry.get("source", "")
        ]
        if integration_titles:
            synthetic_chunk = {
                "source": "https://docs.unitycatalog.io/ai/integrations/",
                "title": "AI Framework Integrations with OSS Unity Catalog / Unity Catalog",
                "content": "\n".join(f"- {title}" for title in integration_titles)
            }
            data.insert(0, synthetic_chunk)
            print(f"✅ Injected synthetic chunk with {len(integration_titles)} integration titles.")
        return data

    def convert_to_langchain_docs(self, data):
        """
        Convert document data from JSON format to LangChain Document objects.
        
        This method transforms the document dictionaries into LangChain Document objects
        with proper page content and metadata structure required for vector store operations.
        
        Args:
            data (list): List of document dictionaries with 'title', 'source', and 'content' keys
            
        Returns:
            list: List of LangChain Document objects with structured content and metadata
        """
        docs = []
        for entry in data:
            title = entry.get("title", "").strip()
            source = entry.get("source", "").strip()
            content = entry.get("content", "").strip()
            full_text = f"\n{content}"
            doc = Document(
                page_content=full_text,
                metadata={
                    "source_url": source,
                    "title": title
                }
            )
            docs.append(doc)
        print(f"✅ Created {len(docs)} LangChain Document objects.")
        return docs

    def build_header_path(self, metadata):
        """
        Build a hierarchical path string from markdown header metadata.
        
        This method creates a breadcrumb-style path from the document's header hierarchy
        (h1 > h2 > h3 > h4) to provide context about the document's structure.
        
        Args:
            metadata (dict): Dictionary containing header information with keys like 'h1', 'h2', etc.
            
        Returns:
            str: A string representing the header hierarchy path, e.g., "Main Topic > Subtopic > Detail"
        """
        return " > ".join(
            [metadata.get(h) for h in ["h1", "h2", "h3", "h4"] if metadata.get(h)]
        )

    def split_documents(self, docs):
        """
        Split documents into smaller chunks based on markdown headers and enrich with section context.
        
        This method uses MarkdownHeaderTextSplitter to break documents into logical sections
        based on their header structure. Each chunk is enriched with section path information
        to provide better context during retrieval. e.g. "[Section: Main Topic > Subtopic]".
        
        Args:
            docs (list): List of LangChain Document objects to split
            
        Returns:
            list: List of smaller Document objects with enriched metadata including section paths
        """
        header_splitter = MarkdownHeaderTextSplitter(
            headers_to_split_on=[("#", "h1"), ("##", "h2"), ("###", "h3"), ("####", "h4")]
        )
        split_docs = []
        for doc in docs:
            header_chunks = header_splitter.split_text(doc.page_content)
            for chunk in header_chunks:
                header_path = self.build_header_path(chunk.metadata)
                enriched_content = f"[Section: {header_path}]\n\n{chunk.page_content}"
                enriched_metadata = {
                    **doc.metadata,
                    **chunk.metadata,
                    "section_path": header_path
                }
                split_docs.append(Document(
                    page_content=enriched_content,
                    metadata=enriched_metadata
                ))
        print(f"🧩 Split into {len(split_docs)} structured chunks.")
        print(f"📝 Example chunk:\n\n{split_docs[0].page_content[:400]}...\n")
        return split_docs

    def build_vector_store(self, augment_synonyms=True, inject_syn_chunks=False, inject_synth_chunk=False):
        """
        Build a complete vector store from document data with various augmentation options.
        
        This is the main method that orchestrates the entire vector store building process:
        loading documents, applying augmentations, splitting into chunks, embedding, and
        storing in a FAISS vector database.
        
        Args:
            augment_synonyms (bool, optional): Whether to augment documents with synonym information. 
                                             Defaults to True.
            inject_syn_chunks (bool, optional): Whether to inject synthetic synonym chunks. 
                                              Defaults to False.
            inject_synth_chunk (bool, optional): Whether to inject synthetic integration summary chunk. 
                                               Defaults to False.
        """
        # Load data
        file_path = os.path.join(self.document_dir, self.document_filename)
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        print(f"📄 Loaded {len(data)} entries.")

        # Optionally inject synthetic or synonym chunks
        if inject_synth_chunk:
            data = self.inject_synthetic_chunk(data)
        if inject_syn_chunks:
            data = self.inject_synonym_chunks(data)
        if augment_synonyms:
            data = self.augment_chunks_with_synonyms(data)

        # Convert and split
        docs = self.convert_to_langchain_docs(data)
        split_docs = self.split_documents(docs)

        # Embed and store in FAISS
        embeddings = OpenAIEmbeddings(api_key=self.openai_api_key)
        vectorstore = FAISS.from_documents(split_docs, embeddings)
        vectorstore.save_local(self.vector_store_path)
        print("✅ FAISS index created and saved locally.")

    def test_vector_store(self, query, k=3):
        
        load_dotenv()
        embeddings = OpenAIEmbeddings(api_key=self.openai_api_key)
        vectorstore = FAISS.load_local(
            self.vector_store_path,
            embeddings=embeddings,
            allow_dangerous_deserialization=True
        )
        results = vectorstore.similarity_search(query, k=k)
        for doc in results:
            print("🔹", doc.metadata["title"])
            print(doc.page_content[:300])
            print("---")


if __name__ == "__main__":
    ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    builder = VectorStoreBuilder(ROOT_DIR, "unitycatalog_ai_grouped_docs.json")
    builder.build_vector_store()
    print("\n🔍 Testing vector store with a sample query...")
    builder.test_vector_store("How do I integrate LangChain with Unity Catalog AI?", k=3)