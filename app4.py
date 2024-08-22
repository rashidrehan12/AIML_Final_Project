import validators
import streamlit as st
from langchain.prompts import PromptTemplate
from langchain_groq import ChatGroq
from langchain.chains.summarize import load_summarize_chain
from langchain.schema import Document
from langchain_community.document_loaders import YoutubeLoader, UnstructuredURLLoader, TextLoader
import pdfplumber
from io import BytesIO
import time

# Streamlit APP Configuration
st.set_page_config(page_title="LangChain: Summarize Reference Content", page_icon="🦜", layout="wide")

# Custom CSS for a dark theme and full-width display
st.markdown("""
    <style>
    /* General layout adjustments for dark theme */
    .main {
        background-color: #121212; /* Dark background for a sleek look */
        padding: 2rem;
        max-width: 100%; /* Ensure full width */
        box-sizing: border-box; /* Ensure padding is included in width */
        color: #e0e0e0; /* Light text color for contrast */
    }

    /* Title and header styling */
    h1 {
        color: #e0e0e0; /* Light text color */
        text-align: center;
        font-family: 'Roboto', sans-serif;
        font-weight: 700;
        margin-bottom: 2rem;
        font-size: 2.5rem; /* Larger font size for the main title */
    }
    h2 {
        color: #e0e0e0; /* Light text color */
        text-align: center;
        font-family: 'Roboto', sans-serif;
        font-weight: 600;
        margin-bottom: 1.5rem;
        font-size: 1.75rem; /* Slightly smaller font size for subheaders */
    }

    /* Sidebar styling */
    .css-1lcbmhc {
        background-color: #1e1e1e; /* Darker sidebar background */
        padding: 25px;
        border-radius: 15px;
        box-shadow: 0 6px 12px rgba(0, 0, 0, 0.3);
        margin-bottom: 20px;
    }

    /* Input box styling */
    .stTextInput, .stTextArea {
        border-radius: 12px; /* Slightly rounded corners */
        border: 1px solid #333333; /* Dark border for input fields */
        padding: 14px; /* Increased padding for better touch */
        background-color: #1e1e1e; /* Dark background for input fields */
        color: #e0e0e0; /* Light text color for input fields */
        font-family: 'Roboto', sans-serif;
        width: 100%; /* Ensure full width */
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2); /* Subtle shadow for depth */
        transition: border-color 0.3s ease, box-shadow 0.3s ease; /* Smooth transition */
    }

    .stTextInput:focus, .stTextArea:focus {
        border-color: #007bb5; /* Highlight border color on focus */
        box-shadow: 0 4px 12px rgba(0, 123, 255, 0.3); /* Enhanced shadow on focus */
        outline: none; /* Remove default outline */
    }

    /* Button styling */
    .stButton>button {
        background-color: #007bb5; /* Primary button color */
        color: #ffffff;
        border-radius: 10px;
        padding: 12px;
        font-size: 16px;
        font-weight: bold;
        transition: background-color 0.3s ease;
        width: 100%;
        border: none; /* Remove border */
    }
    .stButton>button:hover {
        background-color: #005f8a; /* Darker button color on hover */
    }

    /* File uploader styling */
    .stFileUploader {
        border: 1px solid #333333; /* Dark border */
        border-radius: 12px;
        padding: 12px;
        background-color: #1e1e1e; /* Dark background */
        margin-top: 12px;
        width: 100%; /* Ensure full width */
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2); /* Subtle shadow for depth */
    }

    /* Summary box styling */
    .stMarkdown {
        background-color: #1e1e1e; /* Dark background */
        padding: 20px;
        border-left: 6px solid #007bb5; /* Accent color border */
        border-radius: 12px;
        margin-top: 20px;
        font-family: 'Roboto', sans-serif;
        font-size: 16px;
        color: #e0e0e0; /* Light text color */
        box-shadow: 0 6px 12px rgba(0, 0, 0, 0.2); /* Light shadow for depth */
        max-width: 100%; /* Ensure full width */
    }

    /* Success message styling */
    .stAlert {
        background-color: #388e3c; /* Dark green for success messages */
        color: #ffffff;
        font-weight: bold;
        border-radius: 12px;
        padding: 18px;
        box-shadow: 0 2px 5px rgba(0, 0, 0, 0.2); /* Light shadow for depth */
    }

    /* Download button styling */
    .stDownloadButton>button {
        background-color: #007bb5; /* Primary button color */
        color: #ffffff;
        border-radius: 10px;
        padding: 12px;
        width: 100%;
        font-size: 16px;
        font-weight: bold;
        transition: background-color 0.3s ease;
        border: none; /* Remove border */
    }
    .stDownloadButton>button:hover {
        background-color: #005f8a; /* Darker button color on hover */
    }
    </style>
""", unsafe_allow_html=True)



st.title("🦜 LangChain: Summarize Reference Content")
st.subheader('Easily Summarize Content from Various Sources')

# Sidebar for API configuration
with st.sidebar:
    st.header("🔐 API Configuration")
    groq_api_key = st.text_input("Groq API Key", value="", type="password")

# Main content layout with two columns
col1, col2 = st.columns([2, 1])

with col1:
    st.header("🔗 Input Your Data")
    input_urls = st.text_area("Enter URLs (YouTube videos or websites)", "")
    pdf_files = st.file_uploader("Upload PDF files", type="pdf", accept_multiple_files=True)
    text_files = st.file_uploader("Upload Text files", type="txt", accept_multiple_files=True)
    topic_title = st.text_input("Specify Topic or Title")

with col2:
    st.header("⚙️ Actions")

    # Function to process URLs
    def process_urls(urls):
        docs = []
        if urls:
            for url in urls:
                if "youtube.com" in url:
                    loader = YoutubeLoader.from_youtube_url(url, add_video_info=True)
                    video_id = url.split("v=")[-1]
                    thumbnail_url = f"https://img.youtube.com/vi/{video_id}/hqdefault.jpg"
                    st.image(thumbnail_url, caption="YouTube Video Thumbnail", use_column_width=True)
                    docs.extend(loader.load())
                elif validators.url(url):
                    loader = UnstructuredURLLoader(
                        urls=[url],
                        ssl_verify=False,
                        headers={"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 13_5_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36"}
                    )
                    docs.extend(loader.load())
                    st.markdown(f"**Website URL:** [Link]({url})")
                else:
                    st.error(f"Invalid URL: {url}")
        return docs

    # Function to process PDFs
    def process_pdfs(pdf_files):
        docs = []
        if pdf_files:
            for pdf_file in pdf_files:
                with pdfplumber.open(BytesIO(pdf_file.read())) as pdf:
                    text = "\n".join(page.extract_text() for page in pdf.pages if page.extract_text())
                    docs.append(Document(page_content=text))
        return docs

    # Function to process Text files
    def process_texts(text_files):
        docs = []
        if text_files:
            for text_file in text_files:
                text = text_file.read().decode("utf-8")
                docs.append(Document(page_content=text))
        return docs

    # Function to summarize documents
    def summarize_docs(docs, topic_title):
        summaries = []
        try:
            llm = ChatGroq(model="Gemma-7b-It", groq_api_key=groq_api_key)

            # Define the prompt template
            prompt_template = f"""
            Provide a summary of the following content focusing on the topic: "{topic_title}":
            Content:{{text}}
            """
            prompt = PromptTemplate(template=prompt_template, input_variables=["text"])

            # Chain for Summarization
            chain = load_summarize_chain(llm, chain_type="stuff", prompt=prompt)

            # Process content in batches
            max_tokens_per_batch = 500
            batch_size = 5
            for i in range(0, len(docs), batch_size):
                batch = docs[i:i+batch_size]
                try:
                    output_summary = chain.run(batch)
                    summaries.append(output_summary)
                except Exception as e:
                    st.exception(f"An error occurred during summarization: {e}")
                    if "rate limit" in str(e).lower():
                        st.info("Rate limit reached. Retrying after a pause...")
                        time.sleep(300)

            combined_summary = "\n".join(summaries)
            return combined_summary

        except Exception as e:
            st.exception(f"An error occurred: {e}")
            return None

    # Button to process URLs
    if st.button("Summarize URLs"):
        if not groq_api_key.strip() or not topic_title.strip():
            st.error("Please provide the Groq API Key and a topic/title to get started.")
        else:
            urls = [url.strip() for url in input_urls.split('\n') if url.strip()]
            docs = process_urls(urls)
            if docs:
                summary = summarize_docs(docs, topic_title)
                if summary:
                    st.success("Summary generated successfully!")
                    st.markdown(summary)
                    summary_bytes = summary.encode()
                    st.download_button(
                        label="Download Summary",
                        data=summary_bytes,
                        file_name="summary.txt",
                        mime="text/plain"
                    )

    # Button to process PDF files
    if st.button("Summarize PDFs"):
        if not groq_api_key.strip() or not topic_title.strip():
            st.error("Please provide the Groq API Key and a topic/title to get started.")
        else:
            docs = process_pdfs(pdf_files)
            if docs:
                summary = summarize_docs(docs, topic_title)
                if summary:
                    st.success("Summary generated successfully!")
                    st.markdown(summary)
                    summary_bytes = summary.encode()
                    st.download_button(
                        label="Download Summary",
                        data=summary_bytes,
                        file_name="summary.txt",
                        mime="text/plain"
                    )

    # Button to process Text files
    if st.button("Summarize Text Files"):
        if not groq_api_key.strip() or not topic_title.strip():
            st.error("Please provide the Groq API Key and a topic/title to get started.")
        else:
            docs = process_texts(text_files)
            if docs:
                summary = summarize_docs(docs, topic_title)
                if summary:
                    st.success("Summary generated successfully!")
                    st.markdown(summary)
                    summary_bytes = summary.encode()
                    st.download_button(
                        label="Download Summary",
                        data=summary_bytes,
                        file_name="summary.txt",
                        mime="text/plain"
                    )
