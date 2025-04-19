"""
ChatHarvard - Professional Academic Advising System

A sleek, modern implementation of an AI-powered academic advisor for Harvard students.
"""

import streamlit as st
import os
import types
import pandas as pd
import anthropic
import time
import uuid
from typing import List, Dict, Any
import logging
from datetime import datetime

# Configuration
os.environ['TOKENIZERS_PARALLELISM'] = 'false'

try:
    import torch
    if not hasattr(torch, '__path__'):
        torch.__path__ = types.SimpleNamespace(_path=[])
except ImportError:
    pass

# Import the enhanced modules
from database import HarvardDatabase
from course_finder import CourseFinder
from query_processor import QueryProcessor
from context_builder import ContextBuilder
from course_recommender import CourseRecommender

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("chatharvard.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("ChatHarvard")

# File paths
SUBJECTS_FILE = "subjects_rows.csv"
COURSES_FILE = "courses_rows.csv"
Q_REPORTS_FILE_1 = "q_reports_rows_1.csv"
Q_REPORTS_FILE_2 = "q_reports_rows_2.csv"

# Get current year for the copyright footer
current_year = datetime.now().year

# Custom CSS for a professional, sleek design
st.set_page_config(
    page_title="ChatHarvard",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
def load_css():
    css = """
    <style>
        /* Main styling */
        .main {
            background-color: #ffffff;
            color: #1E1E1E;
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
        }
        
        /* App container */
        .block-container {
            max-width: 1200px;
            padding-top: 2rem;
            padding-bottom: 2rem;
        }
        
        /* Header styling */
        .header-container {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 2rem;
            border-bottom: 1px solid #E0E0E0;
            padding-bottom: 1rem;
        }
        
        .logo-container {
            display: flex;
            align-items: center;
        }
        
        .app-title {
            font-size: 1.8rem;
            font-weight: 700;
            color: #8B0000;
            margin-left: 0.5rem;
            letter-spacing: -0.5px;
        }
        
        /* Chat container styling */
        .chat-container {
            background-color: white;
            border-radius: 12px;
            box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
            padding: 1.5rem;
            margin-bottom: 1.5rem;
            border: 1px solid #F0F0F0;
        }
        
        /* Message styling */
        .user-message, .assistant-message {
            padding: 1rem 1.25rem;
            margin-bottom: 1rem;
            border-radius: 12px;
            line-height: 1.5;
            max-width: 90%;
        }
        
        .user-message {
            background-color: #F1F6FF;
            margin-left: auto;
            color: #1E1E1E;
            border: 1px solid #E6EFFD;
        }
        
        .assistant-message {
            background-color: #FCFCFC;
            color: #1E1E1E;
            border: 1px solid #F0F0F0;
            border-left: 3px solid #8B0000;
        }
        
        /* Input box styling */
        .chat-input {
            display: flex;
            padding: 0.75rem;
            border: 1px solid #E0E0E0;
            border-radius: 12px;
            background-color: white;
            box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
            margin-top: 1rem;
        }
        
        .stTextInput > div > div > input {
            border-radius: 8px !important;
            border: 1px solid #E0E0E0 !important;
            padding: 0.75rem 1rem !important;
            font-size: 1rem !important;
        }
        
        .footer {
            text-align: center;
            margin-top: 2rem;
            padding-top: 1rem;
            font-size: 0.8rem;
            color: #6C757D;
            border-top: 1px solid #E0E0E0;
        }
        
        /* Authentication styling */
        .auth-container {
            max-width: 450px;
            margin: 3rem auto;
            padding: 2.5rem;
            background-color: white;
            border-radius: 12px;
            box-shadow: 0 2px 10px rgba(0, 0, 0, 0.08);
            border: 1px solid #F0F0F0;
        }
        
        .auth-title {
            text-align: center;
            margin-bottom: 2rem;
            font-weight: 700;
            font-size: 1.5rem;
            color: #8B0000;
        }
        
        .auth-input {
            margin-bottom: 1.5rem;
        }
        
        .auth-button {
            width: 100%;
            margin-top: 1.5rem;
        }
        
        /* Profile page styling */
        .profile-container {
            background-color: white;
            border-radius: 12px;
            box-shadow: 0 1px 3px rgba(0, 0, 0, 0.08);
            padding: 2rem;
            margin-bottom: 2rem;
            border: 1px solid #F0F0F0;
        }
        
        .profile-title {
            font-weight: 700;
            margin-bottom: 1.5rem;
            font-size: 1.5rem;
            color: #8B0000;
        }
        
        /* Sidebar styling */
        .css-1d391kg, .css-1ssz09n {
            background-color: #FCFCFC;
        }
        
        .css-1629p8f h1 {
            font-size: 1.2rem !important;
            font-weight: 600 !important;
            color: #1E1E1E !important;
        }
        
        .css-1629p8f h2, .css-1629p8f h3 {
            font-size: 1rem !important;
            font-weight: 600 !important;
            color: #1E1E1E !important;
        }
        
        /* Pill badge for status */
        .status-badge {
            display: inline-block;
            padding: 0.35em 0.65em;
            font-size: 0.75em;
            font-weight: 600;
            line-height: 1;
            color: #fff;
            text-align: center;
            white-space: nowrap;
            vertical-align: baseline;
            border-radius: 0.375rem;
        }
        
        .status-badge.connected {
            background-color: #28A745;
        }
        
        .status-badge.disconnected {
            background-color: #DC3545;
        }
        
        /* Avatar */
        .avatar {
            width: 32px;
            height: 32px;
            border-radius: 50%;
            background-color: #8B0000;
            display: flex;
            justify-content: center;
            align-items: center;
            color: white;
            font-weight: 700;
            margin-right: 0.5rem;
            font-size: 14px;
        }
        
        /* Message metadata */
        .message-metadata {
            font-size: 0.8rem;
            color: #6C757D;
            margin-bottom: 0.4rem;
            font-weight: 500;
        }
        
        /* Button styling */
        .stButton > button {
            border-radius: 8px;
            font-weight: 600;
            background-color: #8B0000;
            color: white;
            border: none;
            padding: 0.5rem 1rem;
            transition: all 0.2s ease;
        }
        
        .stButton > button:hover {
            background-color: #6D0000;
            transform: translateY(-1px);
        }
        
        .custom-button {
            display: inline-block;
            padding: 0.5rem 1rem;
            background-color: #8B0000;
            color: white;
            border-radius: 8px;
            text-decoration: none;
            font-weight: 600;
            text-align: center;
            transition: all 0.2s ease;
        }
        
        .custom-button:hover {
            background-color: #6D0000;
            transform: translateY(-1px);
        }
        
        /* Thinking indicator */
        .thinking-indicator {
            display: flex;
            align-items: center;
            margin: 0.5rem 0;
            font-size: 0.9rem;
            color: #6C757D;
        }
        
        .typing-dots {
            display: inline-block;
            margin-left: 0.5rem;
        }
        
        .typing-dot {
            display: inline-block;
            width: 4px;
            height: 4px;
            border-radius: 50%;
            background-color: #6C757D;
            margin-right: 3px;
            animation: typingDot 1.5s infinite ease-in-out;
        }
        
        .typing-dot:nth-child(2) {
            animation-delay: 0.2s;
        }
        
        .typing-dot:nth-child(3) {
            animation-delay: 0.4s;
        }
        
        @keyframes typingDot {
            0%, 60%, 100% { transform: translateY(0); }
            30% { transform: translateY(-4px); }
        }
        
        /* Harvard branding */
        .harvard-branding {
            color: #8B0000;
            font-weight: 700;
        }
        
        /* Fix for selectbox */
        .stSelectbox > div > div > div {
            background-color: white;
        }
        
        /* Welcome message styling */
        .welcome-container {
            background-color: #F7F9FC;
            border-radius: 12px;
            padding: 1.5rem;
            margin-bottom: 2rem;
            border: 1px solid #E6EFFD;
        }
        
        .welcome-title {
            font-size: 1.2rem;
            font-weight: 600;
            color: #1E1E1E;
            margin-bottom: 1rem;
        }
        
        .feature-list {
            margin-bottom: 1rem;
        }
        
        .feature-item {
            display: flex;
            align-items: center;
            margin-bottom: 0.5rem;
        }
        
        .feature-icon {
            margin-right: 0.5rem;
            color: #8B0000;
        }
        
        /* Example queries */
        .example-query {
            display: inline-block;
            margin: 0.25rem;
            padding: 0.4rem 0.75rem;
            background-color: #F1F6FF;
            border-radius: 8px;
            font-size: 0.85rem;
            cursor: pointer;
            border: 1px solid #E6EFFD;
        }
        
        .example-query:hover {
            background-color: #E4EFFF;
        }
        
        /* Feedback buttons */
        .feedback-container {
            display: flex;
            justify-content: flex-end;
            margin-top: 0.5rem;
        }
        
        .feedback-button {
            display: flex;
            align-items: center;
            padding: 0.25rem 0.5rem;
            font-size: 0.8rem;
            color: #6C757D;
            background: none;
            border: none;
            cursor: pointer;
        }
        
        .feedback-button:hover {
            color: #1E1E1E;
        }
        
        .feedback-icon {
            margin-right: 0.25rem;
        }
        
    </style>
    """
    st.markdown(css, unsafe_allow_html=True)
    
load_css()

# Function to create a header with logo
def create_header():
    header_html = """
    <div class="header-container">
        <div class="logo-container">
            <div style="font-size: 2rem;">🎓</div>
            <div class="app-title">ChatHarvard</div>
        </div>
    </div>
    """
    st.markdown(header_html, unsafe_allow_html=True)

# Function to create a footer
def create_footer():
    footer_html = f"""
    <div class="footer">
        <p>© {current_year} ChatHarvard | An AI-powered academic advisor for Harvard students</p>
        <p>Built with <span style="color: #8B0000;">♥</span> using Claude AI</p>
    </div>
    """
    st.markdown(footer_html, unsafe_allow_html=True)

# Authentication functions
def login_page():
    st.markdown('<div class="auth-container">', unsafe_allow_html=True)
    st.markdown('<h2 class="auth-title">Sign In to ChatHarvard</h2>', unsafe_allow_html=True)
    
    auth_method = st.radio("Sign in with:", ["Anthropic API Key", "OpenAI API Key"])
    
    api_key = st.text_input("Enter your API key:", type="password")
    
    if st.button("Sign In", key="login_button"):
        if len(api_key) > 10:  # Very basic validation
            # Generate a session ID
            session_id = str(uuid.uuid4())
            
            # Store API key and session data
            st.session_state.api_key = api_key
            st.session_state.auth_method = auth_method
            st.session_state.authenticated = True
            st.session_state.session_id = session_id
            
            # Initialize empty chat history
            if "chat_history" not in st.session_state:
                st.session_state.chat_history = []
                
            st.success("Authentication successful!")
            st.rerun()
        else:
            st.error("Invalid API key. Please try again.")
    
    st.markdown('</div>', unsafe_allow_html=True)

# Profile setup page
def profile_setup_page():
    st.markdown('<div class="profile-container">', unsafe_allow_html=True)
    st.markdown('<h2 class="profile-title">Set Up Your Academic Profile</h2>', unsafe_allow_html=True)
    
    # Concentration selection
    concentration = st.selectbox(
        "Your Concentration", 
        ["", "Mathematics", "Computer Science", "Economics", "History", "English", "Chemistry", 
         "Physics", "Psychology", "Government", "Sociology", "Other"]
    )
    
    # Year selection
    year = st.selectbox(
        "Your Year",
        ["", "Freshman", "Sophomore", "Junior", "Senior"]
    )
    
    # Courses taken
    courses_taken = st.text_area(
        "Courses you've taken (one per line)",
        height=200
    )
    
    # Academic interests
    interests = st.multiselect(
        "Academic Interests",
        ["Mathematics", "Computer Science", "Data Science", "Economics", "Business", 
         "History", "Literature", "Philosophy", "Physics", "Chemistry", "Biology",
         "Psychology", "Sociology", "Political Science", "International Relations",
         "Arts", "Music", "Film", "Environmental Studies", "Public Health"]
    )
    
    # Learning preferences
    learning_pref = st.multiselect(
        "Learning Preferences",
        ["Lectures", "Seminars", "Project-based", "Lab work", "Reading-intensive",
         "Writing-intensive", "Discussion-based", "Problem sets", "Research-oriented"]
    )
    
    # Submit button
    if st.button("Save Profile"):
        # Store profile data
        courses_list = [course.strip() for course in courses_taken.split("\n") if course.strip()]
        
        st.session_state.student_profile = {
            "concentration": concentration,
            "year": year,
            "courses_taken": courses_list,
            "interests": interests,
            "learning_preferences": learning_pref
        }
        
        st.session_state.profile_setup = True
        st.success("Profile saved successfully!")
        st.rerun()
    
    st.markdown('</div>', unsafe_allow_html=True)

# Main chat interface
def chat_interface():
    # Initialize the database if not already done
    if "db_initialized" not in st.session_state or not st.session_state.db_initialized:
        with st.spinner("Setting up the course database... This may take a few minutes..."):
            try:
                subjects_df, courses_df, q_reports_df = load_data()
                harvard_db = initialize_database(subjects_df, courses_df, q_reports_df)
                
                if harvard_db is not None:
                    st.session_state.harvard_db = harvard_db
                    st.session_state.db_initialized = True
                    
                    # Initialize other components
                    if "last_query_info" not in st.session_state:
                        st.session_state.last_query_info = None
                    if "debug_mode" not in st.session_state:
                        st.session_state.debug_mode = False
                    if "last_context" not in st.session_state:
                        st.session_state.last_context = None
                    if "processing_query" not in st.session_state:
                        st.session_state.processing_query = False
                else:
                    st.error("Failed to initialize database. Please try again.")
                    return
            except Exception as e:
                st.error(f"Error initializing database: {str(e)}")
                return
    
    # Chat container
    st.markdown('<div class="chat-container">', unsafe_allow_html=True)
    
    # Display chat history
    if len(st.session_state.chat_history) == 0:
        # Welcome message
        welcome_html = """
        <div class="welcome-container">
            <div class="welcome-title">👋 Welcome to ChatHarvard!</div>
            <p>I'm your personal Harvard academic advisor. I can help you with:</p>
            <div class="feature-list">
                <div class="feature-item">
                    <span class="feature-icon">✓</span>
                    <span>Course recommendations based on your profile</span>
                </div>
                <div class="feature-item">
                    <span class="feature-icon">✓</span>
                    <span>Information about specific courses and workload</span>
                </div>
                <div class="feature-item">
                    <span class="feature-icon">✓</span>
                    <span>Concentration requirements and planning</span>
                </div>
                <div class="feature-item">
                    <span class="feature-icon">✓</span>
                    <span>Comparing different courses</span>
                </div>
            </div>
            <p>Try asking me something like:</p>
            <div>
                <div class="example-query">I need a 130s level math class for my concentration. What are my options?</div>
                <div class="example-query">What's the easiest way to fulfill my science requirement?</div>
                <div class="example-query">Compare the workload between CS50 and CS51</div>
            </div>
        </div>
        """
        st.markdown(welcome_html, unsafe_allow_html=True)
        
        welcome_msg = {
            "role": "assistant",
            "content": f"""👋 Hi there, {st.session_state.student_profile.get('concentration', '')} student! I'm your Harvard academic advisor.
            
I can help you with:
- Course recommendations based on your interests and profile
- Information about specific courses and their workload
- Concentration requirements
- Comparing different courses
- And much more!

Ask me anything about Harvard academics or try one of these examples:
- "I need a 130s level math class for my concentration. What are my options?"
- "What's the easiest way to fulfill my science requirement?"
- "Compare the workload between CS50 and CS51"
"""
        }
        st.session_state.chat_history.append(welcome_msg)
    
    # Display messages with proper styling
    for i, message in enumerate(st.session_state.chat_history):
        if message["role"] == "user":
            st.markdown(f"""
            <div class="user-message">
                <div class="message-metadata">You</div>
                {message["content"]}
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div class="assistant-message">
                <div class="message-metadata">ChatHarvard</div>
                {message["content"]}
            </div>
            """, unsafe_allow_html=True)
    
    # Add thinking indicator when processing a query
    if st.session_state.get("processing_query", False):
        st.markdown("""
        <div class="thinking-indicator">
            <span>ChatHarvard is thinking</span>
            <span class="typing-dots">
                <span class="typing-dot"></span>
                <span class="typing-dot"></span>
                <span class="typing-dot"></span>
            </span>
        </div>
        """, unsafe_allow_html=True)
    
    # Chat input form - using a form to prevent rerunning on input
    with st.form(key="chat_form", clear_on_submit=True):
        user_input = st.text_input("", placeholder="Ask about Harvard courses, requirements, or get recommendations...", key="chat_input")
        submit = st.form_submit_button("Send")
    
    # Process the query when submitted
    if submit and user_input and not st.session_state.get("processing_query", False):
        # Set processing flag to prevent duplicate runs
        st.session_state.processing_query = True
        
        # Add user message to chat history
        st.session_state.chat_history.append({"role": "user", "content": user_input})
        
        # Force a rerun to show the user message and thinking indicator
        st.rerun()
    
    # If we're processing a query (after the rerun), generate the response
    if st.session_state.get("processing_query", False):
        try:
            # Get the user query (the last user message in chat history)
            user_messages = [msg for msg in st.session_state.chat_history if msg["role"] == "user"]
            if not user_messages:
                st.session_state.processing_query = False
                st.rerun()
                return
                
            query = user_messages[-1]["content"]
            
            # Process the query
            logger.info(f"Processing query: {query}")
            start_time = time.time()
            
            # Create the query processor and process the query
            query_processor = QueryProcessor(query, st.session_state.chat_history, st.session_state.last_query_info)
            query_info = query_processor.process()
            logger.info(f"Query processing completed in {time.time() - start_time:.2f} seconds")
            
            # Find relevant courses
            course_finder = CourseFinder(st.session_state.harvard_db)
            course_results = course_finder.find_courses(query_info, st.session_state.student_profile)
            logger.info(f"Course finding completed in {time.time() - start_time:.2f} seconds")
            
            # Get recommendations
            recommender = CourseRecommender(st.session_state.harvard_db)
            recommendations = recommender.get_recommendations(query_info, st.session_state.student_profile)
            logger.info(f"Recommendations completed in {time.time() - start_time:.2f} seconds")
            
            # Build context
            context_builder = ContextBuilder(
                query_info, 
                course_results, 
                recommendations, 
                st.session_state.student_profile,
                st.session_state.harvard_db
            )
            context = context_builder.build_context()
            st.session_state.last_context = context
            logger.info(f"Context building completed in {time.time() - start_time:.2f} seconds")
            
            # Initialize Anthropic client
            client = anthropic.Anthropic(api_key=st.session_state.api_key)
            
            # Generate response
            response = generate_response(client, query, context, st.session_state.chat_history)
            logger.info(f"Response generation completed in {time.time() - start_time:.2f} seconds")
            
            # Save query info for next turn
            st.session_state.last_query_info = query_info
            
            # Add assistant message to chat history
            st.session_state.chat_history.append({"role": "assistant", "content": response})
            
            # Reset processing flag
            st.session_state.processing_query = False
            
            # Force a rerun to update the chat history
            st.rerun()
            
        except Exception as e:
            # Log the error
            logger.error(f"Error processing query: {str(e)}")
            
            # Add error message to chat history
            error_message = "I'm sorry, I encountered an error while processing your request. Please try again or ask a different question."
            st.session_state.chat_history.append({"role": "assistant", "content": error_message})
            
            # Reset processing flag
            st.session_state.processing_query = False
            
            # Force a rerun to update the chat history
            st.rerun()
    
    st.markdown('</div>', unsafe_allow_html=True)

# Function to load data
@st.cache_data
def load_data():
    """Load all the CSV data files with progress tracking"""
    try:
        logger.info("Loading data files")
        subjects_df = pd.read_csv(SUBJECTS_FILE)
        logger.info(f"Loaded subjects: {len(subjects_df)} rows")
        
        courses_df = pd.read_csv(COURSES_FILE)
        logger.info(f"Loaded courses: {len(courses_df)} rows")
        
        q_reports_df1 = pd.read_csv(Q_REPORTS_FILE_1)
        logger.info(f"Loaded Q reports file 1: {len(q_reports_df1)} rows")
        
        q_reports_df2 = pd.read_csv(Q_REPORTS_FILE_2)
        logger.info(f"Loaded Q reports file 2: {len(q_reports_df2)} rows")
        
        # Combine Q Reports
        q_reports_df = pd.concat([q_reports_df1, q_reports_df2], ignore_index=True)
        logger.info(f"Combined Q reports: {len(q_reports_df)} rows")
        
        return subjects_df, courses_df, q_reports_df
    except Exception as e:
        logger.error(f"Error loading data: {str(e)}")
        raise e

# Function to initialize the database
def initialize_database(subjects_df, courses_df, q_reports_df):
    """Initialize the Harvard database with the data and build advanced indices"""
    try:
        logger.info("Initializing database")
        
        # Create the database object
        harvard_db = HarvardDatabase(subjects_df, courses_df, q_reports_df)
        
        # Process the data
        logger.info("Processing courses")
        harvard_db.process_courses()
        
        logger.info("Processing Q reports")
        harvard_db.process_q_reports()
        
        logger.info("Processing concentrations")
        harvard_db.process_concentrations()
        
        logger.info("Building advanced indexes")
        harvard_db.build_indexes()
        
        logger.info("Database initialization complete")
        return harvard_db
    
    except Exception as e:
        logger.error(f"Error initializing database: {str(e)}")
        return None

# Function to generate response using Anthropic API
def generate_response(client, query, context, conversation_history):
    """Generate a response from Claude based on the query and context"""
    system_prompt = """You are ChatHarvard, a specialized academic advisor for Harvard University students.
    Your purpose is to help students with course selection, academic planning, and understanding 
    degree requirements. Use the provided context about Harvard courses, Q Reports, and degree 
    requirements to give accurate, helpful, and personalized information.
    
    Your responses should be based entirely on the provided context, which contains:
    1. Query analysis - Understanding of the student's question with confidence scores
    2. Retrieval reasoning - How courses were found and ranked based on the query
    3. Course information - Detailed data about relevant courses
    4. Student profile - The student's concentration and courses taken
    
    When answering questions:
    1. Reference specific course codes and names (e.g., MATH 131, CS 124)
    2. Consider the student's concentration and courses already taken
    3. Explain course ratings and workload in context (e.g., 4.5/5.0 is excellent, 8 hours/week is moderate)
    4. Be honest about prerequisites and potential issues flagged in verification sections
    5. Format your answers clearly with appropriate structure
    6. If there are ambiguities or uncertainties noted in the context, acknowledge them
    
    Your goal is to provide well-reasoned, accurate academic advice that helps the student make 
    informed decisions about their course selection and academic path at Harvard.
    
    IMPORTANT: Always use the workload data provided in the context when discussing course workload.
    If there is a workload comparison table, make sure to reference those values explicitly.
    
    Format your answers with Markdown formatting for better readability.
    """
    
    # Convert conversation history to Anthropic's format
    messages = []
    for msg in conversation_history[-10:]:  # Use last 10 messages for context
        messages.append({"role": msg["role"], "content": msg["content"]})
    
    # Add the current question with context
    messages.append({
        "role": "user", 
        "content": f"Based on the following information about Harvard courses and requirements:\n\n{context}\n\nStudent question: {query}"
    })
    
    try:
        logger.info("Generating response with Claude")
        start_time = time.time()
        
        # Use updated model - Claude 3.7 Sonnet
        response = client.messages.create(
            model="claude-3-7-sonnet-20250219",
            max_tokens=2000,
            system=system_prompt,
            messages=messages
        )
        
        end_time = time.time()
        logger.info(f"Response generated in {end_time - start_time:.2f} seconds")
        
        return response.content[0].text
    except Exception as e:
        logger.error(f"Error generating response: {str(e)}")
        # Provide more detailed error message and fallback to other models if needed
        try:
            # Try another model as fallback
            logger.info("Attempting fallback to Claude 3 Opus")
            response = client.messages.create(
                model= "claude-3-5-sonnet-20241022",
                max_tokens=2000,
                system=system_prompt,
                messages=messages
            )
            return response.content[0].text
        except Exception as e2:
            # Try a final fallback
            try:
                logger.info("Attempting final fallback to Claude 3 Haiku")
                response = client.messages.create(
                    model="claude-3-opus-20240229",
                    max_tokens=2000,
                    system=system_prompt,
                    messages=messages
                )
                return response.content[0].text
            except Exception as e3:
                logger.error(f"All fallbacks failed: {str(e3)}")
                return "I'm having trouble generating a response right now. Please check your API key or try again later."

# Sidebar for user profile and settings
with st.sidebar:
    # User profile section
    st.markdown('<h3 style="color: #8B0000; margin-bottom: 1rem;">👤 User Profile</h3>', unsafe_allow_html=True)
    
    # Check if authenticated
    if "authenticated" in st.session_state and st.session_state.authenticated:
        st.markdown(f"""
        <div style="margin-bottom: 1.5rem;">
            <div class="status-badge connected">Connected</div>
            <div style="font-size: 0.9rem; margin-top: 0.5rem;">API: {st.session_state.auth_method}</div>
        </div>
        """, unsafe_allow_html=True)
        
        # Display current profile
        if "profile_setup" in st.session_state and st.session_state.profile_setup:
            st.markdown('<div style="margin-bottom: 1.5rem;">', unsafe_allow_html=True)
            st.markdown(f"<strong>Concentration:</strong> {st.session_state.student_profile.get('concentration', 'Not set')}", unsafe_allow_html=True)
            st.markdown(f"<strong>Year:</strong> {st.session_state.student_profile.get('year', 'Not set')}", unsafe_allow_html=True)
            
            courses_count = len(st.session_state.student_profile.get('courses_taken', []))
            st.markdown(f"<strong>Courses taken:</strong> {courses_count} courses", unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)
            
            # Edit profile button
            if st.button("Edit Profile", key="edit_profile"):
                st.session_state.profile_setup = False
                st.rerun()
        
        # Sign out button
        if st.button("Sign Out", key="sign_out"):
            # Clear session state
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()
    else:
        st.markdown("""
        <div class="status-badge disconnected">Not Connected</div>
        """, unsafe_allow_html=True)
    
    # Settings section
    st.markdown('<h3 style="color: #8B0000; margin-bottom: 1rem;">⚙️ Settings</h3>', unsafe_allow_html=True)
    st.session_state.debug_mode = st.checkbox("Debug Mode", value=st.session_state.get("debug_mode", False))
    
    # Help section
    st.markdown('<h3 style="color: #8B0000; margin-bottom: 1rem;">❓ Help</h3>', unsafe_allow_html=True)
    with st.expander("Example Questions"):
        st.markdown("""
        - "What's a good introductory CS course?"
        - "I'm a Math concentrator, what electives should I take next semester?"
        - "What's the chillest course that fulfills my science requirement?"
        - "Tell me about HIST 1330"
        - "Compare MATH 21a and MATH 23b"
        - "What are the highest-rated ECON courses?"
        """)
    
    with st.expander("About ChatHarvard"):
        st.markdown("""
        <div style="text-align: center; margin-bottom: 1rem;">
            <div style="font-size: 2rem;">🎓</div>
            <div style="font-weight: 700; color: #8B0000; margin-bottom: 0.5rem;">ChatHarvard</div>
        </div>
        
        ChatHarvard is an AI-powered academic advisor for Harvard University students. It helps with course selection, academic planning, and understanding degree requirements.
        
        - Data is based on actual Harvard course catalogs and Q Guide reports
        - All recommendations are personalized to your profile
        - Built using the Claude AI by Anthropic
        """, unsafe_allow_html=True)

# Main app flow
def main():
    create_header()
    
    # Check authentication
    if "authenticated" not in st.session_state or not st.session_state.authenticated:
        login_page()
    elif "profile_setup" not in st.session_state or not st.session_state.profile_setup:
        profile_setup_page()
    else:
        chat_interface()
    
    create_footer()

if __name__ == "__main__":
    main()