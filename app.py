"""
ChatHarvard - Production Backend Server
"""

from flask import Flask, request, jsonify, session

from flask_session import Session
import os
import uuid
import anthropic
import openai
import logging
from datetime import datetime, timedelta
import requests
from functools import wraps
import jwt
from dotenv import load_dotenv
import json
import pandas as pd
import re
import PyPDF2
from io import BytesIO

from flask import Flask, request, jsonify, session, make_response

from dotenv import load_dotenv
load_dotenv()


# Import the enhanced modules
from database import HarvardDatabase
from course_finder import CourseFinder
from query_processor import QueryProcessor
from context_builder import ContextBuilder
from course_recommender import CourseRecommender

# Load environment variables
load_dotenv()

# Configuration
os.environ['TOKENIZERS_PARALLELISM'] = 'false'

# File paths
SUBJECTS_FILE = "subjects_rows.csv"
COURSES_FILE = "courses_rows.csv"
Q_REPORTS_FILE_1 = "q_reports_rows_1.csv"
Q_REPORTS_FILE_2 = "q_reports_rows_2.csv"

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

# Initialize Flask app
app = Flask(__name__, static_folder='frontend/build', static_url_path='')
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'dev_secret_key')
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SESSION_PERMANENT'] = True
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=7)

# Initialize session
Session(app)
# Auth Configuration
ANTHROPIC_CLIENT_ID = os.getenv('ANTHROPIC_CLIENT_ID')
ANTHROPIC_CLIENT_SECRET = os.getenv('ANTHROPIC_CLIENT_SECRET')
ANTHROPIC_REDIRECT_URI = os.getenv('ANTHROPIC_REDIRECT_URI', 'http://localhost:5000/auth/anthropic/callback')

OPENAI_CLIENT_ID = os.getenv('OPENAI_CLIENT_ID')
OPENAI_CLIENT_SECRET = os.getenv('OPENAI_CLIENT_SECRET')
OPENAI_REDIRECT_URI = os.getenv('OPENAI_REDIRECT_URI', 'http://localhost:5000/auth/openai/callback')

JWT_SECRET = os.getenv('JWT_SECRET', 'dev_jwt_secret')

# Global database instance
harvard_db = None

# Authentication middleware
def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        
        # Get token from Authorization header
        if 'Authorization' in request.headers:
            token = request.headers['Authorization'].split(" ")[1]
        elif request.cookies.get('token'):
            token = request.cookies.get('token')

        if not token:
            return jsonify({'message': 'Token is missing!'}), 401
        
        try:
            data = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
            
            # Store decoded values into session for current request
            session['user_id'] = data.get('user_id')
            session['auth_provider'] = data.get('auth_provider')
        except jwt.ExpiredSignatureError:
            return jsonify({'message': 'Token has expired!'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'message': 'Invalid token!'}), 401

        return f(*args, **kwargs)
    
    return decorated

# Initialize database
def initialize_database():
    global harvard_db
    if harvard_db is not None:
        return harvard_db
        
    try:
        logger.info("Loading data files")
        subjects_df = pd.read_csv(SUBJECTS_FILE)
        courses_df = pd.read_csv(COURSES_FILE)
        q_reports_df1 = pd.read_csv(Q_REPORTS_FILE_1)
        q_reports_df2 = pd.read_csv(Q_REPORTS_FILE_2)
        
        # Combine Q Reports
        q_reports_df = pd.concat([q_reports_df1, q_reports_df2], ignore_index=True)
        
        logger.info("Initializing database")
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

# Routes
@app.route('/')
def serve():
    return app.send_static_file('index.html')

# Auth routes
@app.route('/auth/anthropic/login')
def anthropic_login():
    authorization_url = (
        f"https://auth.anthropic.com/oauth2/auth"
        f"?client_id={ANTHROPIC_CLIENT_ID}"
        f"&redirect_uri={ANTHROPIC_REDIRECT_URI}"
        f"&response_type=code"
        f"&scope=claude"
    )
    return jsonify({'auth_url': authorization_url})

@app.route('/auth/anthropic/callback')
def anthropic_callback():
    code = request.args.get('code')
    if not code:
        return jsonify({'error': 'No authorization code provided'}), 400
    
    # Exchange code for token
    try:
        token_url = "https://auth.anthropic.com/oauth2/token"
        payload = {
            'grant_type': 'authorization_code',
            'code': code,
            'redirect_uri': ANTHROPIC_REDIRECT_URI,
            'client_id': ANTHROPIC_CLIENT_ID,
            'client_secret': ANTHROPIC_CLIENT_SECRET
        }
        response = requests.post(token_url, data=payload)
        token_data = response.json()
        
        # Create user session
        user_id = str(uuid.uuid4())
        token = jwt.encode({
            'user_id': user_id,
            'auth_provider': 'anthropic',
            'expires': (datetime.now() + timedelta(days=7)).isoformat()
        }, JWT_SECRET, algorithm="HS256")
        
        # Store authentication info
        session['user_id'] = user_id
        session['auth_provider'] = 'anthropic'
        session['access_token'] = token_data.get('access_token')
        session['refresh_token'] = token_data.get('refresh_token')
        session['id_token'] = token_data.get('id_token')
        
        # Return JWT token and redirect instructions
        return jsonify({
            'token': token,
            'redirect': '/#/profile'
        })
        
    except Exception as e:
        logger.error(f"Auth error: {str(e)}")
        return jsonify({'error': 'Authentication failed'}), 400

@app.route('/auth/openai/login')
def openai_login():
    authorization_url = (
        f"https://auth0.openai.com/authorize"
        f"?client_id={OPENAI_CLIENT_ID}"
        f"&redirect_uri={OPENAI_REDIRECT_URI}"
        f"&response_type=code"
        f"&scope=openid profile email"
    )
    return jsonify({'auth_url': authorization_url})

@app.route('/auth/openai/callback')
def openai_callback():
    code = request.args.get('code')
    if not code:
        return jsonify({'error': 'No authorization code provided'}), 400
    
    # Exchange code for token
    try:
        token_url = "https://auth0.openai.com/oauth/token"
        payload = {
            'grant_type': 'authorization_code',
            'code': code,
            'redirect_uri': OPENAI_REDIRECT_URI,
            'client_id': OPENAI_CLIENT_ID,
            'client_secret': OPENAI_CLIENT_SECRET
        }
        response = requests.post(token_url, data=payload)
        token_data = response.json()
        
        # Create user session
        user_id = str(uuid.uuid4())
        token = jwt.encode({
            'user_id': user_id,
            'auth_provider': 'openai',
            'expires': (datetime.now() + timedelta(days=7)).isoformat()
        }, JWT_SECRET, algorithm="HS256")
        
        # Store authentication info
        session['user_id'] = user_id
        session['auth_provider'] = 'openai'
        session['access_token'] = token_data.get('access_token')
        session['refresh_token'] = token_data.get('refresh_token')
        session['id_token'] = token_data.get('id_token')
        
        # Return JWT token and redirect instructions
        return jsonify({
            'token': token,
            'redirect': '/#/profile'
        })
        
    except Exception as e:
        logger.error(f"Auth error: {str(e)}")
        return jsonify({'error': 'Authentication failed'}), 400

@app.route('/api/auth/logout', methods=['POST'])
@token_required
def logout():
    # Clear session data
    session.clear()
    return jsonify({'message': 'Logged out successfully'})

@app.route('/api/auth/verify', methods=['GET'])
@token_required
def verify_auth():
    return jsonify({
        'authenticated': True,
        'user_id': session.get('user_id'),
        'auth_provider': session.get('auth_provider')
    })

# Profile routes
@app.route('/api/profile', methods=['GET'])
@token_required
def get_profile():
    user_id = session.get('user_id')
    profile_path = f"user_data/{user_id}/profile.json"
    
    try:
        if os.path.exists(profile_path):
            with open(profile_path, 'r') as f:
                profile = json.load(f)
            return jsonify(profile)
        else:
            return jsonify({
                'concentration': '',
                'year': '',
                'courses_taken': [],
                'interests': [],
                'learning_preferences': []
            })
    except Exception as e:
        logger.error(f"Error getting profile: {str(e)}")
        return jsonify({'error': 'Could not retrieve profile'}), 500

@app.route('/api/profile', methods=['POST'])
@token_required
def save_profile():
    user_id = session.get('user_id')
    profile_dir = f"user_data/{user_id}"
    profile_path = f"{profile_dir}/profile.json"
    
    try:
        os.makedirs(profile_dir, exist_ok=True)
        
        profile = request.json
        with open(profile_path, 'w') as f:
            json.dump(profile, f)
            
        return jsonify({'message': 'Profile saved successfully'})
    except Exception as e:
        logger.error(f"Error saving profile: {str(e)}")
        return jsonify({'error': 'Could not save profile'}), 500

# Chat routes
@app.route('/api/chat/history', methods=['GET'])
@token_required
def get_chat_history():
    user_id = session.get('user_id')
    history_path = f"user_data/{user_id}/chat_history.json"
    
    try:
        if os.path.exists(history_path):
            with open(history_path, 'r') as f:
                history = json.load(f)
            return jsonify(history)
        else:
            # Return an empty array if no history exists
            return jsonify([])
    except Exception as e:
        logger.error(f"Error getting chat history: {str(e)}")
        return jsonify({'error': 'Could not retrieve chat history'}), 500

@app.route('/api/chat/message', methods=['POST'])
@token_required
def send_message():
    user_id = session.get('user_id')
    user_dir = f"user_data/{user_id}"
    history_path = f"{user_dir}/chat_history.json"
    last_query_path = f"{user_dir}/last_query.json"
    
    # Ensure user directory exists
    os.makedirs(user_dir, exist_ok=True)
    
    try:
        # Get message from request
        data = request.json
        message = data.get('message')
        
        # Load chat history
        chat_history = []
        if os.path.exists(history_path):
            with open(history_path, 'r') as f:
                chat_history = json.load(f)
        
        # Add user message to history
        chat_history.append({"role": "user", "content": message})
        
        # Load last query info
        last_query_info = None
        if os.path.exists(last_query_path):
            with open(last_query_path, 'r') as f:
                last_query_info = json.load(f)
        
        # Load user profile
        profile_path = f"{user_dir}/profile.json"
        student_profile = {}
        if os.path.exists(profile_path):
            with open(profile_path, 'r') as f:
                student_profile = json.load(f)
        
        # Initialize database if needed
        if harvard_db is None:
            initialize_database()
        
        # Process the query
        logger.info(f"Processing query: {message}")
        query_processor = QueryProcessor(message, chat_history, last_query_info)
        query_info = query_processor.process()
        
        # Find relevant courses
        course_finder = CourseFinder(harvard_db)
        course_results = course_finder.find_courses(query_info, student_profile)
        
        # Get recommendations
        recommender = CourseRecommender(harvard_db)
        recommendations = recommender.get_recommendations(query_info, student_profile)
        
        # Build context
        context_builder = ContextBuilder(
            query_info, 
            course_results, 
            recommendations, 
            student_profile,
            harvard_db
        )
        context = context_builder.build_context()
        
        # Generate response using appropriate client based on auth provider
        auth_provider = session.get('auth_provider')
        access_token = session.get('access_token')
        
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
        
        # Prepare messages for the API
        messages = []
        for msg in chat_history[-10:]:  # Use last 10 messages for context
            messages.append({"role": msg["role"], "content": msg["content"]})
        
        # Add the current question with context
        messages.append({
            "role": "user", 
            "content": f"Based on the following information about Harvard courses and requirements:\n\n{context}\n\nStudent question: {message}"
        })
        
        # Choose API client based on auth provider
        ai_response = None
        if auth_provider == 'anthropic':
            client = anthropic.Anthropic(api_key=access_token)
            response = client.messages.create(
                model="claude-3-7-sonnet-20250219",
                max_tokens=2000,
                system=system_prompt,
                messages=messages
            )
            ai_response = response.content[0].text
        elif auth_provider == 'openai':
            client = openai.Client(api_key=access_token)
            response = client.chat.completions.create(
                model="gpt-4-turbo",
                messages=[{"role": "system", "content": system_prompt}] + messages,
                max_tokens=2000
            )
            ai_response = response.choices[0].message.content
        else:
            ai_response = "Error: Unable to generate response due to authentication issue."
            
        # Add assistant's response to history
        chat_history.append({"role": "assistant", "content": ai_response})
        course_code_match = re.search(r'\b([A-Za-z]{2,4})\s*(\d{1,3}[A-Za-z]*)\b', message)
        if course_code_match:
            course_code = f"{course_code_match.group(1).upper()} {course_code_match.group(2)}"
            course = harvard_db.get_course_by_code(course_code)
            if course:
                chat_history[-1]['courseData'] = course
                
        # Save updated history
        with open(history_path, 'w') as f:
            json.dump(chat_history, f)
            
        # Save query info for next time
        with open(last_query_path, 'w') as f:
            json.dump(query_info, f)
            
        return jsonify({
            "response": ai_response, 
            "history": chat_history
        })
        
    except Exception as e:
        logger.error(f"Error processing message: {str(e)}")
        return jsonify({'error': 'Could not process message'}), 500

@app.route('/api/chat/clear', methods=['POST'])
@token_required
def clear_chat():
    user_id = session.get('user_id')
    history_path = f"user_data/{user_id}/chat_history.json"
    
    try:
        # Create an empty chat history
        if os.path.exists(history_path):
            os.remove(history_path)
            
        return jsonify({'message': 'Chat history cleared successfully'})
    except Exception as e:
        logger.error(f"Error clearing chat: {str(e)}")
        return jsonify({'error': 'Could not clear chat history'}), 500

@app.route('/api/auth/set_api_key', methods=['POST', 'OPTIONS'])
def set_api_key():
    origin = request.headers.get('Origin', '')
    
    def corsify(response):
        response.headers['Access-Control-Allow-Origin'] = origin if origin == 'http://localhost:3000' else ''
        response.headers['Access-Control-Allow-Credentials'] = 'true'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type,Authorization'
        response.headers['Access-Control-Allow-Methods'] = 'POST,OPTIONS'
        return response

    if request.method == 'OPTIONS':
        return corsify(make_response('', 200))

    try:
        data = request.get_json()
        if not data:
            return corsify(jsonify({'error': 'No data provided'})), 400

        api_key = data.get('api_key')
        provider = data.get('provider')

        if provider not in ['openai', 'anthropic']:
            return corsify(jsonify({'error': 'Invalid provider'})), 400

        user_id = str(uuid.uuid4())
        session['user_id'] = user_id
        session['auth_provider'] = provider

        if api_key:
            if provider == 'openai' and not api_key.startswith('sk-'):
                return corsify(jsonify({'error': 'Invalid OpenAI API key format'})), 400
            elif provider == 'anthropic' and not api_key.startswith(('sk-ant-', 'sk-ant-api')):
                return corsify(jsonify({'error': 'Invalid Anthropic API key format'})), 400
            session['access_token'] = api_key
        else:
            default_key = os.getenv(f'DEFAULT_{provider.upper()}_API_KEY')
            if not default_key:
                return corsify(jsonify({'error': f'No default {provider} key available'})), 400
            session['access_token'] = default_key

        token = jwt.encode({
            'user_id': user_id,
            'auth_provider': provider,
            'expires': (datetime.now() + timedelta(days=7)).isoformat()
        }, JWT_SECRET, algorithm="HS256")

        os.makedirs(f"user_data/{user_id}", exist_ok=True)
        return corsify(jsonify({'token': token, 'user_id': user_id}))

    except Exception as e:
        logger.error(f"Error in set_api_key: {str(e)}")
        return corsify(jsonify({'error': f'Server error: {str(e)}'})), 500


# Concentration data route
@app.route('/api/concentrations', methods=['GET'])
@token_required
def get_concentrations():
    # Initialize database if needed
    if harvard_db is None:
        initialize_database()
        
    try:
        concentrations = list(harvard_db.concentration_dict.keys())
        return jsonify(concentrations)
    except Exception as e:
        logger.error(f"Error getting concentrations: {str(e)}")
        return jsonify({'error': 'Could not retrieve concentrations'}), 500


@app.after_request
def apply_cors(response):
    origin = request.headers.get('Origin')
    if origin in ["http://localhost:3000", "https://chat-harvard.vercel.app"]:
        response.headers['Access-Control-Allow-Origin'] = origin
        response.headers['Access-Control-Allow-Credentials'] = 'true'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type,Authorization'
        response.headers['Access-Control-Allow-Methods'] = 'GET,POST,OPTIONS,PUT,DELETE'
    return response

@app.route('/api/auth/validate_key', methods=['POST', 'OPTIONS'])
def validate_api_key():
    """
    Validates an API key without creating a session
    """
    # For OPTIONS request, return preflight response
    if request.method == 'OPTIONS':
        response = jsonify({'status': 'success'})
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
        response.headers.add('Access-Control-Allow-Methods', 'POST,OPTIONS')
        return response
    
    # For POST request, process normally
    # Add explicit CORS headers
    response_headers = {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Headers': 'Content-Type,Authorization',
        'Access-Control-Allow-Methods': 'POST,OPTIONS'
    }
    
    data = request.get_json()
    api_key = data.get('api_key')
    provider = data.get('provider')
    
    # Log the request for debugging
    logger.info(f"Validating API key for provider: {provider}")

    if provider not in ['openai', 'anthropic']:
        logger.warning(f"Invalid provider requested: {provider}")
        response = jsonify({'valid': False, 'error': 'Invalid provider'}), 400
        for key, value in response_headers.items():
            response[0].headers[key] = value
        return response

    if not api_key:
        # If no key provided, check if we have a default one
        default_key = os.getenv(f'DEFAULT_{provider.upper()}_API_KEY')
        if default_key:
            logger.info(f"Using default {provider} key")
            response = jsonify({'valid': True})
            for key, value in response_headers.items():
                response.headers[key] = value
            return response
        else:
            logger.warning(f"No API key provided and no default key available for {provider}")
            response = jsonify({'valid': False, 'error': 'No API key provided and no default key available'}), 400
            for key, value in response_headers.items():
                response[0].headers[key] = value
            return response

    # Simple validation based on format without API calls
    valid = False
    error_message = 'Invalid API key format'
    
    try:
        if provider == 'openai':
            if api_key.startswith('sk-'):
                valid = True
                logger.info("OpenAI API key format is valid")
            else:
                error_message = 'OpenAI API key should start with sk-'
                logger.warning("Invalid OpenAI API key format")
        elif provider == 'anthropic':
            if api_key.startswith(('sk-ant-', 'sk-ant-api')):
                valid = True
                logger.info("Anthropic API key format is valid")
            else:
                error_message = 'Anthropic API key should start with sk-ant-'
                logger.warning("Invalid Anthropic API key format")
    except Exception as e:
        logger.error(f"API key validation error: {str(e)}")
        error_message = 'API key validation failed: ' + str(e)
        valid = False

    if valid:
        response = jsonify({'valid': True})
        for key, value in response_headers.items():
            response.headers[key] = value
        return response
    else:
        response = jsonify({'valid': False, 'error': error_message}), 400
        for key, value in response_headers.items():
            response[0].headers[key] = value
        return response

@app.route('/api/extract_courses', methods=['POST', 'OPTIONS'])
@token_required
def extract_courses_from_pdf():
    """
    Extract course codes from a PDF transcript
    """
    # For OPTIONS request, return preflight response
    if request.method == 'OPTIONS':
        response = jsonify({'status': 'success'})
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
        response.headers.add('Access-Control-Allow-Methods', 'POST,OPTIONS')
        return response
        
    if 'pdf' not in request.files:
        return jsonify({'error': 'No PDF file provided'}), 400
    
    pdf_file = request.files['pdf']
    
    if pdf_file.filename == '':
        return jsonify({'error': 'No PDF file selected'}), 400
    
    try:
        # Read PDF content
        pdf_bytes = pdf_file.read()
        pdf_file_obj = BytesIO(pdf_bytes)
        
        # Parse PDF
        pdf_reader = PyPDF2.PdfReader(pdf_file_obj)
        text_content = ""
        
        # Extract text from all pages
        for page_num in range(len(pdf_reader.pages)):
            page = pdf_reader.pages[page_num]
            text_content += page.extract_text()
        
        # Regular expression to find course codes
        # This pattern looks for common Harvard course code formats
        # Adjust as needed based on actual transcript formats
        course_pattern = r'\b([A-Za-z]{2,4})\s*(\d{1,3}[A-Za-z]{0,2})\b'
        matches = re.findall(course_pattern, text_content)
        
        # Format the matches
        courses = []
        for dept, num in matches:
            course_code = f"{dept.upper()} {num}"
            courses.append(course_code)
        
        # Remove duplicates while preserving order
        unique_courses = []
        for course in courses:
            if course not in unique_courses:
                unique_courses.append(course)
        
        return jsonify({'courses': unique_courses})
    
    except Exception as e:
        logger.error(f"Error extracting courses from PDF: {str(e)}")
        return jsonify({'error': f'Failed to process PDF: {str(e)}'}), 500

# Add a route to handle shared links
@app.route('/api/shared/<share_id>', methods=['GET', 'OPTIONS'])
def get_shared_profile(share_id):
    """
    Get a read-only shared profile by its ID
    """
    # For OPTIONS request, return preflight response
    if request.method == 'OPTIONS':
        response = jsonify({'status': 'success'})
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
        response.headers.add('Access-Control-Allow-Methods', 'GET,OPTIONS')
        return response
        
    try:
        # This is a simplified implementation - in a real app, you would
        # look up the share_id in a database to get the associated user data
        # Here we're just returning a mock profile
        
        # For now, just validate that share_id is alphanumeric
        if not re.match(r'^[a-zA-Z0-9]+$', share_id):
            return jsonify({'error': 'Invalid share ID'}), 400
            
        # In a real implementation, you would fetch this data from a database
        # based on the share_id
        return jsonify({
            'isShared': True,
            'shareId': share_id,
            'profile': {
                'concentration': 'Computer Science',
                'year': 'Junior',
                'courses_taken': ['CS 50', 'MATH 21A', 'ECON 10A'],
                'interests': ['Machine Learning', 'Economics'],
            },
            'chatHistory': [
                {"role": "user", "content": "What courses should I take next semester?"},
                {"role": "assistant", "content": "Based on your profile, I'd recommend considering CS 124, CS 121, or if you're interested in machine learning, CS 181."}
            ]
        })
    except Exception as e:
        logger.error(f"Error getting shared profile: {str(e)}")
        return jsonify({'error': 'Failed to retrieve shared profile'}), 500

@app.route('/api/courses/<course_code>', methods=['GET'])
@token_required
def get_course_by_code(course_code):
    # Decode URL-encoded spaces (e.g., MATH%20121 → MATH 121)
    course_code = course_code.replace('%20', ' ').upper()
    
    try:
        # Initialize DB if needed
        if harvard_db is None:
            initialize_database()

        course = harvard_db.get_course_by_code(course_code)
        if course:
            return jsonify(course)
        else:
            return jsonify({'error': 'Course not found'}), 404
    except Exception as e:
        logger.error(f"Error getting course by code: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500


if __name__ == "__main__":
    # Initialize the database on startup
    initialize_database()
    
    # Create user_data directory
    os.makedirs("user_data", exist_ok=True)
    
    # Run the app
    app.run(debug=True, host="0.0.0.0", port=5050)

