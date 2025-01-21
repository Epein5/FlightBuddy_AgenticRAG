import streamlit as st
import os
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.vectorstores import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain.retrievers.multi_query import MultiQueryRetriever
from langchain.retrievers.document_compressors import EmbeddingsFilter
from langchain.retrievers import ContextualCompressionRetriever
import sqlite3
import pandas as pd

# Page configuration
st.set_page_config(
    page_title="Airline Information System",
    page_icon="✈️",
    layout="wide"
)

# Custom CSS with dark theme
st.markdown("""
    <style>
    /* Dark theme colors */
    :root {
        --background-color: #1a1a1a;
        --text-color: #ffffff;
        --primary-color: #2d2d2d;
        --secondary-color: #404040;
        --accent-color: #4CAF50;
    }
    
    /* Main container */
    .main {
        background-color: var(--background-color);
        color: var(--text-color);
        padding: 2rem;
    }
    
    /* Header styling */
    h1, h2, h3 {
        color: #ffffff !important;
    }
    
    /* Tab styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 2rem;
        background-color: var(--primary-color);
        border-radius: 0.5rem;
        padding: 0.5rem;
    }
    
    .stTabs [data-baseweb="tab"] {
        height: 4rem;
        color: var(--text-color) !important;
    }
    
    /* Query type indicators */
    .query-type {
        padding: 0.75rem 1.5rem;
        border-radius: 0.5rem;
        font-weight: bold;
        margin-bottom: 1rem;
        text-align: center;
    }
    
    .rag {
        background-color: #1e4620;
        color: #4CAF50;
        border: 1px solid #2e7031;
    }
    
    .sql {
        background-color: #1e3a5f;
        color: #64B5F6;
        border: 1px solid #2196F3;
    }
    
    .general {
        background-color: #5f4c1e;
        color: #FFC107;
        border: 1px solid #FFC107;
    }
    
    /* Response box */
    .response-box {
        background-color: #2d2d2d;
        color: #e0e0e0;
        padding: 1.5rem;
        border-radius: 0.5rem;
        border: 1px solid #404040;
        margin-top: 1rem;
        line-height: 1.6;
    }
    
    /* Input field */
    .stTextInput input {
        background-color: #2d2d2d;
        color: white;
        border: 1px solid #404040;
    }
    
    .stTextInput input:focus {
        border-color: #4CAF50;
        box-shadow: 0 0 0 1px #4CAF50;
    }
    
    /* Button styling */
    .stButton button {
        background-color: #4CAF50 !important;
        color: white !important;
        border: none !important;
        padding: 0.5rem 2rem !important;
        font-weight: bold !important;
    }
    
    .stButton button:hover {
        background-color: #45a049 !important;
        border: none !important;
    }
    
    /* System info card */
    .system-info {
        background-color: var(--primary-color);
        padding: 1.5rem;
        border-radius: 0.5rem;
        border: 1px solid var(--secondary-color);
    }
    
    /* Footer */
    .footer {
        text-align: center;
        padding: 1rem;
        color: #888888;
        margin-top: 2rem;
    }
    
    /* Link colors */
    a {
        color: #4CAF50 !important;
    }
    
    /* Spinner */
    .stSpinner {
        color: #4CAF50 !important;
    }
    </style>
""", unsafe_allow_html=True)

# Load environment variables
load_dotenv()

# Initialize LLM
api_key = os.getenv("GEMINI_API_KEY")
llm = ChatGoogleGenerativeAI(model="gemini-pro", api_key=api_key)

# Initialize embeddings
embedding_function = HuggingFaceEmbeddings(
    model_name="BAAI/bge-large-en-v1.5",
    model_kwargs={'device': 'cpu'}
)


# Prompts (same as before)
ai_assistant_prompt = """
You are an AI assistant that responds strictly with a single word (use_rag, use_sql use_nth) based on the following rules:
    * Respond with use_rag if the prompt concerns the rules, regulations,services provided by Tribhuvan International Airport or any thing_related to Airports.
    * Respond with use_sql if the prompt relates to booking of flight tickets.
    * Respond with use_nth if the prompt is unrelated to Tribhuvan International Airport or if it is a general-purpose query (e.g., greetings, casual conversation).
Your response must always be a single word: (use_rag or use_sql or use_nth). No additional text or explanation is allowed.
"""

rag_prompt = """
You are an advanced AI assistant capable of answering queries based on the provided context. Use the retrieved context to generate accurate and concise responses. Follow these rules:

1. Only use the retrieved context to answer the query. Do not make assumptions or add information not found in the context.
2. If the retrieved context does not contain enough information to answer the query, respond with: "I'm sorry, the context does not provide enough information to answer this question."

### Retrieved Context:
{retrieved_context}

### Query:
{query}

### Response:
"""

sql_prompt = """
### Prompt for the LLM:
You are an intelligent assistant specializing in processing and analyzing flight data. Below is the retrieved flight information and the user query. Your task is to interpret the user's request, analyze the flight data, and provide a concise and accurate response.

### Retrieved Flight Information:
{flight_data}

### User Query:
{user_query}

### Guidelines:
1. Use the flight data provided to answer the query.
2. If multiple flights match the query, list them all.
3. If no flights match, clearly state so.
4. Provide additional helpful details, such as estimated times, types (Domestic or International), or death rates if relevant to the query.
5. Format your response in a user-friendly and readable way.
6. Give answer like this:
    * If there is a flight from Kathmandu to Pokhara, then the answer should be: "There is a flight from Kathmandu to Pokhara." then give the rest of the details.
    * If there are multiple flights from Kathmandu to Pokhara, then the answer should be: "There are multiple flights from Kathmandu to Pokhara."then give the rest of the details.
    * If there are no flights from Kathmandu to Pokhara, then the answer should be: "There are no flights from Kathmandu to Pokhara."
"""

# Helper functions (same as before)
def ai_assistant(prompt, query, llm):
    llm_query = prompt + query
    return llm.invoke(llm_query).content

def rag_assistant(rag_prompt, query, llm):
    db = Chroma(
        persist_directory="output/Airpott.db",
        embedding_function=embedding_function
    )
    retriever = db.as_retriever()
    embeddings_filter = EmbeddingsFilter(embeddings=embedding_function, similarity_threshold=0.6)
    compression_retriever = ContextualCompressionRetriever(
        base_compressor=embeddings_filter,
        base_retriever=retriever
    )
    compressed_docs = compression_retriever.get_relevant_documents(query=query)
    unique_answers = {i.metadata['answer'] for i in compressed_docs}
    final_docs = "\n".join(unique_answers)
    final_rag_prompt = rag_prompt.format(retrieved_context=final_docs, query=query)
    return llm.invoke(final_rag_prompt).content

def sql_agent_prompt(query):
    return f"""
        You are an intelligent SQL agent specializing in generating concise SQL queries to retrieve flight information from a database named 'Nepali_Airlines_Data.db'. Your role is to interpret the user's query and produce an accurate, functional SQL query. 

        ### Guidelines:
        1. Assume the database table is named `Nepali_Airlines_Data` with the following columns:
        - `Airline Name`: Name of the airline.
        - `From`: Departure location.
        - `To`: Arrival location.
        - `EstimatedTakeOffTime`: Scheduled departure time.
        - `EstimatedArrivalTime`: Scheduled arrival time.
        - `Type`: Indicates if the flight is "Domestic" or "International".
        - `DeathRate`: Death rate percentage.

        2. Understand the user's requirements and generate an appropriate SQL query.
        3. Return **only** the SQL query as output, enclosed in double quotes (`"`).
        4. Ensure the query is correct, concise, and formatted properly.

        ### Example Query:
        User Query: "I want to book a ticket from Chitwan to Lumbini."
        Response:
        SELECT * FROM Nepali_Airlines_Data WHERE `From` = 'Chitwan' AND `To` = 'Lumbini'

        Your Task:
        1. Read the user query provided as input.
        2. Interpret the query requirements and identify relevant filtering conditions.
        3. Generate a valid SQL query to retrieve the required information.
        4. The generated SQL query should include all the informations about the flight from the database.

        Input Query: "{query}"

        Output Query: """

def sql_items_retrieval(sql_agent_prompt, query, llm, sql_prompt):
    llm_query = sql_agent_prompt(query)
    sql_query = llm.invoke(llm_query).content.replace('"', '')
    conn = sqlite3.connect("DB/Nepali_Airlines_Data.db")
    df = pd.read_sql_query(sql_query, conn)
    final_sql_query = sql_prompt.format(flight_data=df.to_string(), user_query=query)
    return llm.invoke(final_sql_query).content

def normal_query(query, llm):
    return llm.invoke(query).content
#Streamlit UI
st.title("✈️ Airline Information System")
st.markdown('<p style="color: #888888;">Ask questions about flight bookings, airport regulations, or general aviation queries!</p>', unsafe_allow_html=True)

# Create tabs for different query types
col1, col2 = st.columns([2, 1])

with col1:
    tabs = ["Query System", "Help"]
    selected_tab = st.tabs(tabs)

    with selected_tab[0]:
        user_query = st.text_input("Enter your query:", placeholder="e.g., What items are not allowed in luggage?")
        
        if st.button("Submit Query", use_container_width=True):
            with st.spinner("Processing your query..."):
                try:
                    decision = ai_assistant(ai_assistant_prompt, user_query, llm)
                    
                    # Display query type with custom styling
                    if decision == "use_rag":
                        st.markdown('<div class="query-type rag">Using: Airport Regulations & Information System (RAG)</div>', unsafe_allow_html=True)
                    elif decision == "use_sql":
                        st.markdown('<div class="query-type sql">Using: Flight Database System (SQL)</div>', unsafe_allow_html=True)
                    else:
                        st.markdown('<div class="query-type general">Using: General Knowledge System</div>', unsafe_allow_html=True)
                    
                    # Get and display response
                    if decision == "use_rag":
                        response = rag_assistant(rag_prompt, user_query, llm)
                    elif decision == "use_sql":
                        response = sql_items_retrieval(sql_agent_prompt, user_query, llm, sql_prompt)
                    else:
                        response = normal_query(user_query, llm)
                    
                    # Format the response with proper line breaks
                    formatted_response = response.replace('\n', '<br>')
                    st.markdown(f'<div class="response-box">{formatted_response}</div>', unsafe_allow_html=True)
                    
                except Exception as e:
                    st.error(f"An error occurred: {str(e)}")

    with selected_tab[1]:
        st.markdown("""
        <div class="system-info">
        <h3>How to Use</h3>
        <p>1. <strong>Flight Bookings</strong>: Ask about available flights, schedules, and routes</p>
        <p>2. <strong>Airport Rules</strong>: Inquire about luggage restrictions, security procedures, and regulations</p>
        <p>3. <strong>General Queries</strong>: Ask any aviation-related questions</p>
        
        <h3>Example Queries</h3>
        <ul>
        <li>"What items are not allowed in checked baggage?"</li>
        <li>"Show me flights from Kathmandu to Pokhara"</li>
        <li>"What are the rules for carrying liquids?"</li>
        </ul>
        </div>
        """, unsafe_allow_html=True)

with col2:
    st.markdown("""
    <div class="system-info">
    <h3>System Information</h3>
    <p>This system uses three different methods to answer your queries:</p>
    
    <p><strong>1. Airport Regulations & Information (RAG)</strong></p>
    <ul>
    <li>Handles questions about airport rules</li>
    <li>Provides information about procedures</li>
    <li>Answers regulation-related queries</li>
    </ul>
    
    <p><strong>2. Flight Database (SQL)</strong></p>
    <ul>
    <li>Searches flight schedules</li>
    <li>Provides booking information</li>
    <li>Shows available routes</li>
    </ul>
    
    <p><strong>3. General Knowledge</strong></p>
    <ul>
    <li>Answers general aviation questions</li>
    <li>Provides travel-related information</li>
    <li>Handles miscellaneous queries</li>
    </ul>
    </div>
    """, unsafe_allow_html=True)

# Add footer
st.markdown("---")
st.markdown('<div class="footer">Powered by LangChain and Gemini-Pro 🚀</div>', unsafe_allow_html=True)