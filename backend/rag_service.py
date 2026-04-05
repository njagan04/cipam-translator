from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.prompts import PromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser
import os

# Load env variables (e.g., GOOGLE_API_KEY)
load_dotenv()

# In-memory store for MVP. 
# For production, we'd map session_ids to distinct vector databases.
vector_store = None

def index_document(text: str) -> bool:
    """
    Chunks the translated text and embeds it into the FAISS vector database.
    """
    global vector_store
    try:
        # Prevent indexing if API key is missing
        if not os.getenv("GOOGLE_API_KEY"):
            raise ValueError("GOOGLE_API_KEY not found in environment variables.")

        print("Chunking document...")
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=150)
        chunks = text_splitter.split_text(text)
        
        if not chunks:
            return False

        print(f"Creating embeddings for {len(chunks)} chunks...")
        embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001")
        vector_store = FAISS.from_texts(chunks, embeddings)
        print("Indexing complete.")
        return True
    except Exception as e:
        print(f"Error indexing document: {e}")
        return False

def format_docs(docs):
    return "\n\n".join(doc.page_content for doc in docs)

def chat_with_document(query: str, lang: str) -> str:
    """
    Retrieves the most similar chunks from FAISS and asks Gemini to answer in the target language.
    """
    global vector_store
    if not vector_store:
        return "Document not indexed. Please make sure the file was successfully translated."
    
    try:
        if not os.getenv("GOOGLE_API_KEY"):
             return "Server configuration error: GOOGLE_API_KEY is missing."

        # Initialize the LLM (Gemini 1.5 Flash provides good speed and native multilingual abilities)
        llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash", temperature=0.3)
        
        # Set up retrieval
        retriever = vector_store.as_retriever(search_kwargs={"k": 4})
        
        # Create prompt forcing output in the requested language
        template = f"""You are an expert AI assistant specializing in answering questions based on the provided CIPAM Intellectual Property document.
Use the following pieces of retrieved context to answer the question at the end. 
Keep your answer accurate and helpful. If the answer is not contained in the context, explicitly state that you don't know based on the document. Do not invent external information.

CRITICAL INSTRUCTION: You MUST provide your final answer entirely in the following language: {lang}.

Context:
{{context}}

Question: {{input}}
Answer in {lang}:"""

        prompt = PromptTemplate.from_template(template)
        
        # Build the RAG chain using LCEL (LangChain Expression Language)
        rag_chain = (
            {"context": retriever | format_docs, "input": RunnablePassthrough()}
            | prompt
            | llm
            | StrOutputParser()
        )
        
        print(f"Querying Gemini inside FAISS for: '{query}' in language: {lang}")
        response = rag_chain.invoke(query)
        
        return response
    except Exception as e:
        print(f"Error in chat: {e}")
        return f"An error occurred while thinking: {str(e)}"
