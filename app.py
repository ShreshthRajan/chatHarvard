# ChatHarvard - Main Application
# This file contains the Streamlit interface and main application logic

import streamlit as st
import os
import pandas as pd
import anthropic
from typing import List, Dict, Any

# Import the other modules
from database import HarvardDatabase
from course_finder import CourseFinder
from query_processor import QueryProcessor
from context_builder import ContextBuilder
from course_recommender import CourseRecommender

# Set up page
st.set_page_config(page_title="ChatHarvard", page_icon="🎓", layout="wide")
st.title("ChatHarvard")
st.write("Your Harvard academic planning assistant")

# Set up application directories
if not os.path.exists("data"):
    os.makedirs("data")

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
    """Load all the CSV data files"""
    subjects_df = pd.read_csv(SUBJECTS_FILE)
    courses_df = pd.read_csv(COURSES_FILE)
    q_reports_df1 = pd.read_csv(Q_REPORTS_FILE_1)
    q_reports_df2 = pd.read_csv(Q_REPORTS_FILE_2)
    
    # Combine Q Reports
    q_reports_df = pd.concat([q_reports_df1, q_reports_df2], ignore_index=True)
    
    return subjects_df, courses_df, q_reports_df

# Function to initialize the database
def initialize_database(subjects_df, courses_df, q_reports_df):
    """Initialize the Harvard database with the data"""
    try:
        st.info("Setting up the course database... This may take a few minutes...")
        
        # Create the database object
        harvard_db = HarvardDatabase(subjects_df, courses_df, q_reports_df)
        
        # Process and index the data
        progress_bar = st.progress(0)
        total_steps = 4
        
        # Step 1: Process courses
        harvard_db.process_courses()
        progress_bar.progress(1/total_steps)
        
        # Step 2: Process Q reports
        harvard_db.process_q_reports()
        progress_bar.progress(2/total_steps)
        
        # Step 3: Process subjects/concentrations
        harvard_db.process_concentrations()
        progress_bar.progress(3/total_steps)
        
        # Step 4: Build indexes
        harvard_db.build_indexes()
        progress_bar.progress(4/total_steps)
        
        st.success("Database initialization complete!")
        return harvard_db
    
    except Exception as e:
        st.error(f"Error initializing database: {str(e)}")
        return None

# Function to generate response using Anthropic API
def generate_response(query, context, conversation_history):
    """Generate a response from Claude based on the query and context"""
    system_prompt = """You are ChatHarvard, a specialized assistant for Harvard University students.
    Your purpose is to help students with course selection, academic planning, and understanding 
    degree requirements. Use the provided context about Harvard courses, Q Reports, and degree 
    requirements to give accurate, helpful information.
    
    When answering questions:
    1. Reference specific course codes and names when appropriate (e.g., MATH 131, CS 124)
    2. Consider the student's concentration and courses already taken
    3. For course recommendations:
       - Prioritize courses with good ratings (overall_score_course_mean)
       - Pay attention to workload (mean_hours)
       - Consider the course level and prerequisites
       - Be specific about which term/semester courses are offered
    4. Be honest when you don't have enough information to answer a question
    5. Format your answers clearly and concisely
    6. If asked about "130s level" courses, understand this refers to courses numbered 130-139
    7. Course numbers indicate level: 100-level are undergraduate courses, 200-level are graduate
    8. Provide context about workload: mean_hours indicates the average hours per week students spend
    
    Harvard course Q report data includes:
    - overall_score_course_mean: Rating of the course (higher is better, on a scale of 1-5)
    - mean_hours: Average hours per week students spend on the course
    - comments: Student feedback on the course
    
    When comparing courses to find the "easiest" or most manageable:
    - Lower mean_hours generally indicates less time commitment
    - Higher overall_score_course_mean generally indicates better student experience
    - Consider both factors together when making recommendations
    
    Always answer based on the actual course data provided in the context. If the context includes
    information about specific courses, use that information rather than making general statements.
    """
    
    # Convert conversation history to Anthropic's format
    messages = []
    for msg in conversation_history[-5:]:  # Use last 5 messages for context
        messages.append({"role": msg["role"], "content": msg["content"]})
    
    # Add the current question with context
    messages.append({"role": "user", "content": f"Based on the following information about Harvard courses and requirements:\n\n{context}\n\nStudent question: {query}"})
    
    try:
        # Use the latest Claude model
        response = client.messages.create(
            model="claude-3-7-sonnet-20240307",
            max_tokens=1000,
            system=system_prompt,
            messages=messages
        )
        return response.content[0].text
    except Exception as e:
        # Provide more detailed error message and fallback to other models if needed
        try:
            # Try another model as fallback
            response = client.messages.create(
                model="claude-3-5-sonnet-20240620",
                max_tokens=1000,
                system=system_prompt,
                messages=messages
            )
            return response.content[0].text
        except Exception as e2:
            return f"Error generating response: {str(e)}. Fallback also failed: {str(e2)}. Please check your Anthropic API key and try again."

# Sidebar for student profile
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
            # Create the query processor and process the query
            query_processor = QueryProcessor(query, st.session_state.chat_history, st.session_state.last_query_info)
            query_info = query_processor.process()
            
            # Find relevant courses using the course finder
            course_finder = CourseFinder(st.session_state.harvard_db)
            course_results = course_finder.find_courses(query_info, st.session_state.student_profile)
            
            # Get course recommendations if needed
            recommender = CourseRecommender(st.session_state.harvard_db)
            recommendations = recommender.get_recommendations(query_info, st.session_state.student_profile)
            
            # Build the context for the LLM
            context_builder = ContextBuilder(
                query_info, 
                course_results, 
                recommendations, 
                st.session_state.student_profile,
                st.session_state.harvard_db
            )
            context = context_builder.build_context()
            
            # Generate response
            response = generate_response(query, context, st.session_state.chat_history)
            
            # Save current query info for reference in future turns
            st.session_state.last_query_info = query_info
            
            # Display response
            st.write(response)
            
            # Add assistant message to chat history
            st.session_state.chat_history.append({"role": "assistant", "content": response})

# Show student profile in the main area
if st.session_state.student_profile["concentration"]:
    st.write("---")
    st.subheader("Your Current Profile")
    st.write(f"**Concentration:** {st.session_state.student_profile['concentration']}")
    
    if st.session_state.student_profile["courses_taken"]:
        st.write("**Courses taken:**")
        for course in st.session_state.student_profile["courses_taken"]:
            st.write(f"- {course}")