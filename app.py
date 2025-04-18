"""
ChatHarvard - Enhanced Academic Advising System

This file contains the Streamlit interface and main application logic
with advanced retrieval and reasoning capabilities.
"""

import streamlit as st
import os
import types
import pandas as pd
import anthropic
import time
from typing import List, Dict, Any
import logging

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

# Set up page
st.set_page_config(page_title="ChatHarvard", page_icon="🎓", layout="wide")
st.title("ChatHarvard")
st.write("Your Harvard academic planning assistant")

# Set up application directories
if not os.path.exists("data"):
    os.makedirs("data")
if not os.path.exists("data/embeddings_cache"):
    os.makedirs("data/embeddings_cache")

# Initialize session state
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "db_initialized" not in st.session_state:
    st.session_state.db_initialized = False
if "student_profile" not in st.session_state:
    st.session_state.student_profile = {
        "concentration": "",
        "courses_taken": []
    }
if "harvard_db" not in st.session_state:
    st.session_state.harvard_db = None
if "last_query_info" not in st.session_state:
    st.session_state.last_query_info = None
if "debug_mode" not in st.session_state:
    st.session_state.debug_mode = False
if "load_status" not in st.session_state:
    st.session_state.load_status = None

# File paths
SUBJECTS_FILE = "subjects_rows.csv"
COURSES_FILE = "courses_rows.csv"
Q_REPORTS_FILE_1 = "q_reports_rows_1.csv"
Q_REPORTS_FILE_2 = "q_reports_rows_2.csv"

# ANTHROPIC API KEY
# You can input your API key in the sidebar or add it directly below
ANTHROPIC_API_KEY = st.sidebar.text_input("Enter your Anthropic API key:", type="password")
if not ANTHROPIC_API_KEY:
    st.warning("Please enter your Anthropic API key in the sidebar to use ChatHarvard")
    st.stop()

# Initialize anthropic client
client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

# Function to load and process data
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
        st.info("Setting up the enhanced course database... This may take a few minutes...")
        logger.info("Initializing database")
        
        # Create the database object
        harvard_db = HarvardDatabase(subjects_df, courses_df, q_reports_df)
        
        # Process and index the data with progress tracking
        progress_bar = st.progress(0)
        total_steps = 4
        
        # Step 1: Process courses
        logger.info("Processing courses")
        harvard_db.process_courses()
        progress_bar.progress(1/total_steps)
        
        # Step 2: Process Q reports
        logger.info("Processing Q reports")
        harvard_db.process_q_reports()
        progress_bar.progress(2/total_steps)
        
        # Step 3: Process subjects/concentrations
        logger.info("Processing concentrations")
        harvard_db.process_concentrations()
        progress_bar.progress(3/total_steps)
        
        # Step 4: Build advanced indexes (including vector search)
        logger.info("Building advanced indexes")
        st.session_state.load_status = st.empty()
        st.session_state.load_status.info("Building vector search indices (this might take a few minutes)...")
        harvard_db.build_indexes()
        st.session_state.load_status.empty()
        progress_bar.progress(4/total_steps)
        
        st.success("Database initialization complete!")
        logger.info("Database initialization complete")
        return harvard_db
    
    except Exception as e:
        logger.error(f"Error initializing database: {str(e)}")
        st.error(f"Error initializing database: {str(e)}")
        return None

# Function to generate response using Anthropic API
# Updated generate_response function with current model versions
def generate_response(query, context, conversation_history):
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
            model="claude-3-7-sonnet-20250219",  # UPDATED MODEL
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
                model= "claude-3-5-sonnet-20241022",  # UPDATED FALLBACK MODEL
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

# Sidebar for student profile and settings
with st.sidebar:
    st.header("Your Academic Profile")
    
    # Concentration selection
    concentration = st.selectbox(
        "Your Concentration", 
        ["", "Mathematics", "Computer Science", "Economics", "History", "English", "Chemistry", 
         "Physics", "Psychology", "Government", "Sociology", "Other"]
    )
    
    # Courses taken
    courses_taken = st.text_area(
        "Courses you've taken (one per line)",
        height=200
    )
    
    # Update profile button
    if st.button("Update Profile"):
        st.session_state.student_profile["concentration"] = concentration
        st.session_state.student_profile["courses_taken"] = [
            course.strip() for course in courses_taken.split("\n") if course.strip()
        ]
        st.success("Profile updated!")
    
    # Advanced settings
    st.header("Advanced Settings")
    st.session_state.debug_mode = st.checkbox("Debug Mode", value=st.session_state.debug_mode)
    
    if st.session_state.debug_mode:
        st.info("Debug mode enabled. Additional information will be displayed.")

# Main area - Initialize the database if not already done
if not st.session_state.db_initialized:
    st.info("Initializing database for the first time...")
    subjects_df, courses_df, q_reports_df = load_data()
    harvard_db = initialize_database(subjects_df, courses_df, q_reports_df)
    
    if harvard_db is not None:
        st.session_state.harvard_db = harvard_db
        st.session_state.db_initialized = True
        st.rerun()
    else:
        st.error("Failed to initialize database. Please check the error messages above.")
        st.stop()

# Display chat history
for message in st.session_state.chat_history:
    with st.chat_message(message["role"]):
        st.write(message["content"])

# Chat input
query = st.chat_input("Ask about Harvard courses, requirements, or get recommendations")

if query:
    # Add user message to chat history
    st.session_state.chat_history.append({"role": "user", "content": query})
    
    # Display user message
    with st.chat_message("user"):
        st.write(query)
    
    # Generate response
    with st.chat_message("assistant"):
        with st.spinner("Analyzing and generating response..."):
            logger.info(f"Processing query: {query}")
            start_time = time.time()
            
            # Create the query processor and process the query
            query_processor = QueryProcessor(query, st.session_state.chat_history, st.session_state.last_query_info)
            query_info = query_processor.process()
            logger.info(f"Query processing completed in {time.time() - start_time:.2f} seconds")
            
            if st.session_state.debug_mode:
                st.write("**Query Analysis:**")
                st.json(query_info)
            
            # Find relevant courses using the enhanced course finder
            course_finder = CourseFinder(st.session_state.harvard_db)
            course_results = course_finder.find_courses(query_info, st.session_state.student_profile)
            logger.info(f"Course finding completed in {time.time() - start_time:.2f} seconds")
            
            if st.session_state.debug_mode:
                st.write("**Course Results:**")
                st.write(f"Found {len(course_results.get('relevant_courses', []))} relevant courses")
                if course_results.get("retrieval_explanation"):
                    st.write("Retrieval process:")
                    for step in course_results.get("retrieval_explanation"):
                        st.write(f"- {step}")
            
            # Get course recommendations if needed
            recommender = CourseRecommender(st.session_state.harvard_db)
            recommendations = recommender.get_recommendations(query_info, st.session_state.student_profile)
            logger.info(f"Recommendations completed in {time.time() - start_time:.2f} seconds")
            
            if st.session_state.debug_mode and recommendations.get("recommended_courses"):
                st.write("**Recommendations:**")
                st.write(f"Found {len(recommendations.get('recommended_courses', []))} recommended courses")
                if recommendations.get("explanation"):
                    for exp in recommendations.get("explanation")[:3]:  # Show just first few explanation steps
                        st.write(f"- {exp}")
            
            # Build the context for the LLM
            context_builder = ContextBuilder(
                query_info, 
                course_results, 
                recommendations, 
                st.session_state.student_profile,
                st.session_state.harvard_db
            )
            context = context_builder.build_context()
            logger.info(f"Context building completed in {time.time() - start_time:.2f} seconds")
            
            if st.session_state.debug_mode:
                st.write("**Context Length:**")
                st.write(f"{len(context)} characters")
                
                # Show a sample of the context
                st.expander("View Context Sample (first 500 chars)").write(context[:500] + "...")
            
            # Generate response
            response = generate_response(query, context, st.session_state.chat_history)
            logger.info(f"Response generation completed in {time.time() - start_time:.2f} seconds")
            
            # Save current query info for reference in future turns
            st.session_state.last_query_info = query_info
            
            # Display response
            st.write(response)
            
            # Add assistant message to chat history
            st.session_state.chat_history.append({"role": "assistant", "content": response})
            
            if st.session_state.debug_mode:
                st.write(f"**Total processing time:** {time.time() - start_time:.2f} seconds")

# Show student profile in the main area
if st.session_state.student_profile["concentration"]:
    st.write("---")
    st.subheader("Your Current Profile")
    st.write(f"**Concentration:** {st.session_state.student_profile['concentration']}")
    
    if st.session_state.student_profile["courses_taken"]:
        st.write("**Courses taken:**")
        for course in st.session_state.student_profile["courses_taken"]:
            st.write(f"- {course}")

# Help section
with st.expander("Help & Tips"):
    st.write("""
    ## How to use ChatHarvard
    
    1. **Set up your profile** in the sidebar by selecting your concentration and adding courses you've already taken
    2. **Ask questions** about Harvard courses, such as:
       - "What's the easiest MATH 130-level course next semester?"
       - "Recommend CS courses with good ratings and manageable workload"
       - "What are the requirements for a Mathematics concentration?"
       - "Tell me about ECON 1010"
    3. **Get personalized recommendations** based on your profile and preferences
    
    ## Example Questions
    
    - "What's a good introductory CS course?"
    - "I'm a Math concentrator, what electives should I take next semester?"
    - "What's the chillest course that fulfills my science requirement?"
    - "Tell me about HIST 1330"
    - "Compare MATH 21a and MATH 23b"
    - "What are the highest-rated ECON courses?"
    """)