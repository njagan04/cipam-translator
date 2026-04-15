from dotenv import load_dotenv
import os
import math

# Load env variables (e.g., GOOGLE_API_KEY)
load_dotenv()

# Lightning-fast pure-Python in-memory chunk store (bypasses massive FAISS overheads natively)
chunks_global = []

def index_document(text: str) -> bool:
    """
    Chunks the translated text algorithmically without loading heavy ML weights.
    """
    global chunks_global
    try:
        if not os.getenv("GOOGLE_API_KEY"):
            raise ValueError("GOOGLE_API_KEY not found in environment variables.")

        print("Executing ultra-fast mathematical array chunking...")
        chunks_global = []
        words = text.split(" ")
        current = []
        size = 0
        limit = 1000 # Roughly 1000 chars per pure chunk naturally
        for w in words:
            if size + len(w) + 1 > limit and current:
                chunks_global.append(" ".join(current))
                current = [w]
                size = len(w)
            else:
                current.append(w)
                size += len(w) + 1
        if current:
            chunks_global.append(" ".join(current))
            
        print(f"Indexing complete instantly! {len(chunks_global)} native chunks mapped.")
        return True
    except Exception as e:
        print(f"Error indexing document: {e}")
        return False

def retrieve_top_k(query: str, k: int = 4) -> str:
    global chunks_global
    if not chunks_global: return ""
    # Ultra-high-speed pure Python Term Frequency matching algorithm
    query_words = set([w.strip().lower() for w in query.split()])
    scores = []
    for chunk in chunks_global:
        chunk_words = chunk.lower().split()
        score = sum(chunk_words.count(qw) for qw in query_words)
        scores.append((score, chunk))
    scores.sort(key=lambda x: x[0], reverse=True)
    return "\n\n".join([c for s, c in scores[:min(k, len(scores))]])

def chat_with_document(query: str, lang: str) -> str:
    """
    Retrieves the most similar chunks algorithmically and asks Gemini to synthesize the final answer.
    """
    global chunks_global
    if not chunks_global:
        return "Document not indexed. Please make sure the file was successfully translated."
    
    try:
        if not os.getenv("GOOGLE_API_KEY"):
             return "Server configuration error: GOOGLE_API_KEY is missing."

        from langchain_google_genai import ChatGoogleGenerativeAI
        from langchain_core.prompts import PromptTemplate
        from langchain_core.output_parsers import StrOutputParser
        llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0.3)
        
        # Pull matching context literally instantly without PyTorch!
        context = retrieve_top_k(query, k=4)
        
        # Execute Gemini inference!
        template = f"""You are an expert AI assistant specializing in answering questions based on the provided CIPAM Intellectual Property document.
Use the following pieces of retrieved context to answer the question at the end. 
Keep your answer accurate and helpful. If the answer is not contained in the context, explicitly state that you don't know based on the document. Do not invent external information.

CRITICAL INSTRUCTION: You MUST provide your final answer entirely in the following language: {lang}.

Context:
{context}

Question: {query}
Answer in {lang}:"""

        prompt = PromptTemplate.from_template(template)
        
        # Simplified native execution flow
        rag_chain = prompt | llm | StrOutputParser()
        
        print(f"Querying Gemini (Bypassing PyTorch execution locks) for: '{query}' in language: {lang}")
        response = rag_chain.invoke({})
        
        return response
    except Exception as e:
        print(f"Error in chat: {e}")
        return f"An error occurred while thinking: {str(e)}"
