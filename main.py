import os
import streamlit as st
import pickle
import time
from dotenv import load_dotenv

from langchain.chains import RetrievalQAWithSourcesChain
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.document_loaders import UnstructuredURLLoader
from langchain.embeddings import HuggingFaceEmbeddings
from langchain.vectorstores import FAISS
from langchain_mistralai.chat_models import ChatMistralAI  # ✅ Mistral LLM

# Load environment variables (especially MISTRAL_API_KEY)
load_dotenv()

# Streamlit UI
st.title("FinQueryBot: News Research Tool 📈")
st.sidebar.title("News Article URLs")

urls = []
for i in range(3):
    url = st.sidebar.text_input(f"URL {i+1}")
    urls.append(url)

process_url_clicked = st.sidebar.button("Process URLs")
file_path = "faiss_store_mistral.pkl"

main_placeholder = st.empty()

# Initialize Mistral Chat LLM
llm = ChatMistralAI(temperature=0.9, max_tokens=500)

if process_url_clicked:
    # Load data
    loader = UnstructuredURLLoader(urls=urls)
    main_placeholder.text("🔄 Loading data from URLs...")
    data = loader.load()

    # Split text
    text_splitter = RecursiveCharacterTextSplitter(
        separators=['\n\n', '\n', '.', ','],
        chunk_size=1000,
        chunk_overlap=200
    )
    main_placeholder.text("✂️ Splitting text into chunks...")
    docs = text_splitter.split_documents(data)

    # Generate embeddings with HuggingFace model
    main_placeholder.text("🧠 Creating embeddings with HuggingFace model...")
    embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
    vectorstore_hf = FAISS.from_documents(docs, embeddings)

    # Save vector index
    with open(file_path, "wb") as f:
        pickle.dump(vectorstore_hf, f)

    main_placeholder.success("✅ URLs processed and FAISS index saved!")

# Query input
query = main_placeholder.text_input("Ask a question based on the articles:")
if query:
    if os.path.exists(file_path):
        with open(file_path, "rb") as f:
            vectorstore = pickle.load(f)
            retriever = vectorstore.as_retriever()

            chain = RetrievalQAWithSourcesChain.from_chain_type(
                llm=llm,
                retriever=retriever
            )

            result = chain.invoke({"question": query})
            st.header("Answer")
            st.write(result["answer"])

            sources = result.get("sources", "")
            if sources:
                st.subheader("Sources:")
                for source in sources.split("\n"):
                    st.write(source)
    else:
        st.error("FAISS index not found. Please process the URLs first.")