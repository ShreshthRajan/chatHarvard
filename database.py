"""
database.py - Enhanced Database Module for Harvard Course Data

This module provides a comprehensive database interface for Harvard course data, 
with fast lookups, efficient processing, and vector-based semantic search capabilities.
"""

import pandas as pd
import re
import numpy as np
from typing import Dict, List, Optional, Tuple, Set, Any, Union
import os
import pickle
import logging
from nltk.tokenize import word_tokenize as nltk_word_tokenize

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("HarvardDatabase")

# Try to import optional dependencies with fallbacks
try:
    from sentence_transformers import SentenceTransformer
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    logger.warning("sentence-transformers not available, vector search will be disabled")
    SENTENCE_TRANSFORMERS_AVAILABLE = False

try:
    import faiss
    FAISS_AVAILABLE = True
except ImportError:
    logger.warning("faiss not available, vector search will be disabled")
    FAISS_AVAILABLE = False

try:
    from sklearn.feature_extraction.text import TfidfVectorizer
    SKLEARN_AVAILABLE = True
except ImportError:
    logger.warning("scikit-learn not available, some features will be limited")
    SKLEARN_AVAILABLE = False

try:
    from rank_bm25 import BM25Okapi
    BM25_AVAILABLE = True
except ImportError:
    logger.warning("rank_bm25 not available, BM25 search will be disabled")
    BM25_AVAILABLE = False

try:
    import nltk
    NLTK_AVAILABLE = True

    # Set the download directory to a location within the project
    nltk_data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "nltk_data")
    os.makedirs(nltk_data_dir, exist_ok=True)

    # Important: update path *before* calling `find()` or `download`
    nltk.data.path = [nltk_data_dir] + nltk.data.path

    # Download required NLTK resources with proper error handling
    def download_nltk_resource(resource):
        try:
            nltk.data.find(resource)
            logger.info(f"NLTK resource {resource} already downloaded")
        except LookupError:
            logger.info(f"Downloading NLTK resource: {resource}")
            nltk.download(resource, download_dir=nltk_data_dir, quiet=True)

    # Correct NLTK resources
    download_nltk_resource('punkt')
    download_nltk_resource('stopwords')

    # Now import after ensuring availability
    try:
        from nltk.tokenize import word_tokenize
        from nltk.corpus import stopwords
    except ImportError:
        logger.warning("Failed to import NLTK modules after download")
        NLTK_AVAILABLE = False
    
except ImportError:
    logger.warning("nltk not available, text tokenization will use basic split")
    NLTK_AVAILABLE = False

def safe_word_tokenize(text: str) -> List[str]:
    try:
        return nltk_word_tokenize(text)
    except Exception as e:
        logger.warning(f"Falling back to basic tokenization due to error: {e}")
        return text.lower().split()

class HarvardDatabase:
    """Enhanced database for Harvard courses with vector search capabilities"""
    
    def __init__(self, subjects_df, courses_df, q_reports_df):
        """Initialize with the raw dataframes"""
        self.subjects_df = subjects_df
        self.courses_df = courses_df  
        self.q_reports_df = q_reports_df
        
        # Processed data structures
        self.merged_courses = None  # Will hold course data merged with Q reports
        self.course_dict = {}  # Will hold courses indexed by course_id
        self.dept_course_dict = {}  # Will hold courses indexed by department and number
        self.concentration_dict = {}  # Will hold concentration data
        
        # Lookup tables
        self.course_by_code = {}  # Maps course codes (e.g., "MATH 136") to course_ids
        self.course_by_name = {}  # Maps course names to course_ids
        self.courses_by_level = {}  # Maps (dept, level) to lists of course_ids
        self.courses_by_term = {}  # Maps terms to lists of course_ids
        
        # Track processed IDs to avoid duplicates
        self.processed_ids = set()
        
        # Vector search components
        self.model = None  # Sentence transformer model for embeddings
        self.course_embeddings = None  # Course embeddings for vector search
        self.course_ids_for_embeddings = []  # Course IDs corresponding to embeddings
        self.embedding_index = None  # FAISS index for efficient vector search
        
        # BM25 for lexical search
        self.bm25_index = None  # BM25 index for keyword search
        self.tokenized_corpus = []  # Tokenized course texts
        self.course_ids_for_bm25 = []  # Course IDs corresponding to BM25 index
        
        # Cached search results
        self.search_cache = {}  # Cache for search results
        
        # Embedding cache directory
        self.cache_dir = "data/embeddings_cache"
        if not os.path.exists(self.cache_dir):
            os.makedirs(self.cache_dir)
    
    def process_courses(self) -> None:
        """Process and clean course data"""
        try:
            # Clean the courses dataframe
            self.courses_df = self.courses_df.dropna(subset=['class_name', 'course_id'])
            
            # Extract course information
            for _, row in self.courses_df.iterrows():
                course_id = row['course_id']
                
                # Skip if we've already processed this ID
                if course_id in self.processed_ids:
                    continue
                    
                self.processed_ids.add(course_id)
                
                # Store course in dictionary
                self.course_dict[course_id] = row.to_dict()
                
                # Extract department and number
                class_tag = row.get('class_tag', '')
                if isinstance(class_tag, str):
                    # Try to extract department and number
                    match = re.search(r'([A-Za-z]+)\s*(\d+)', class_tag)
                    if match:
                        dept = match.group(1).upper()
                        num = int(match.group(2))
                        
                        # Store by department and number
                        key = (dept, num)
                        if key not in self.dept_course_dict:
                            self.dept_course_dict[key] = []
                        self.dept_course_dict[key].append(course_id)
                        
                        # Store by course code
                        course_code = f"{dept} {num}"
                        self.course_by_code[course_code] = course_id
                        
                        # Store by level
                        level = (num // 10) * 10  # E.g., 136 -> 130
                        level_key = (dept, level)
                        if level_key not in self.courses_by_level:
                            self.courses_by_level[level_key] = []
                        self.courses_by_level[level_key].append(course_id)
                
                # Store by name
                class_name = row.get('class_name', '')
                if isinstance(class_name, str) and class_name:
                    self.course_by_name[class_name.lower()] = course_id
                
                # Store by term
                term = row.get('term', '')
                if isinstance(term, str) and term:
                    if term not in self.courses_by_term:
                        self.courses_by_term[term] = []
                    self.courses_by_term[term].append(course_id)
                    
            logger.info(f"Processed {len(self.course_dict)} courses")
            
        except Exception as e:
            logger.error(f"Error processing courses: {str(e)}")
            raise
    
    def process_q_reports(self) -> None:
        """Process Q reports and merge with course data"""
        try:
            # Clean the Q reports dataframe
            self.q_reports_df = self.q_reports_df.dropna(subset=['course_id'])
            
            # Convert course_id to integer for joining
            self.q_reports_df['course_id'] = self.q_reports_df['course_id'].astype(int)
            
            # Create a working copy of course data
            courses_working = pd.DataFrame.from_dict(self.course_dict, orient='index')
            
            # Convert course_id to int for joining
            if 'course_id' in courses_working.columns:
                courses_working['course_id'] = courses_working['course_id'].astype(int)
            
            # Merge course data with Q reports
            self.merged_courses = courses_working.merge(
                self.q_reports_df[['course_id', 'overall_score_course_mean', 'mean_hours', 'comments']],
                on='course_id',
                how='left'
            )
            
            # Update the course dictionary with the Q report data
            for _, row in self.merged_courses.iterrows():
                course_id = row['course_id']
                if course_id in self.course_dict:
                    # Update with Q report data
                    self.course_dict[course_id].update({
                        'overall_score_course_mean': row.get('overall_score_course_mean'),
                        'mean_hours': row.get('mean_hours'),
                        'comments': row.get('comments')
                    })
                    
            logger.info(f"Processed Q reports for {len(self.merged_courses)} courses")
            
        except Exception as e:
            logger.error(f"Error processing Q reports: {str(e)}")
            raise
    
    def process_concentrations(self) -> None:
        """Process concentration data"""
        try:
            # Clean the subjects dataframe
            self.subjects_df = self.subjects_df.dropna(subset=['subject'])
            
            # Process each concentration
            for _, row in self.subjects_df.iterrows():
                subject = row['subject']
                
                # Skip if we've already processed this concentration
                if subject in self.concentration_dict:
                    continue
                
                # Store concentration data
                self.concentration_dict[subject] = {
                    'department': row.get('department', ''),
                    'ab0': row.get('ab0', ''),
                    'ab1': row.get('ab1', ''),
                    'ab2': row.get('ab2', '')
                }
                
            logger.info(f"Processed {len(self.concentration_dict)} concentrations")
            
        except Exception as e:
            logger.error(f"Error processing concentrations: {str(e)}")
            raise
    
    def build_indexes(self) -> None:
        """Build advanced indexes for search and retrieval with better error handling"""
        try:
            # Basic indices are always built
            logger.info("Building basic indices")
            
            # Advanced indices are built only if dependencies are available
            if SENTENCE_TRANSFORMERS_AVAILABLE and FAISS_AVAILABLE:
                logger.info("Building vector search indices")
                
                # Initialize the sentence transformer model with explicit error checking
                try:
                    self.model = self._load_embedding_model()
                    if self.model is None:
                        logger.error("Failed to load embedding model")
                        raise ValueError("Embedding model could not be loaded")
                        
                    # Check if we have cached embeddings
                    cache_file = os.path.join(self.cache_dir, "course_embeddings.pkl")
                    if os.path.exists(cache_file):
                        try:
                            with open(cache_file, 'rb') as f:
                                cache_data = pickle.load(f)
                                self.course_embeddings = cache_data.get('embeddings')
                                self.course_ids_for_embeddings = cache_data.get('ids')
                            logger.info("Loaded cached embeddings")
                            
                            # Important: Build the FAISS index after loading cached embeddings
                            if self.course_embeddings is not None and len(self.course_embeddings) > 0:
                                dimension = self.course_embeddings.shape[1]
                                self.embedding_index = faiss.IndexFlatL2(dimension)
                                self.embedding_index.add(self.course_embeddings)
                                logger.info("Built FAISS index from cached embeddings")
                            else:
                                logger.warning("Cached embeddings are empty or invalid")
                                self._build_vector_search_index()
                        except Exception as e:
                            logger.error(f"Error loading cached embeddings: {e}")
                            self._build_vector_search_index()
                    else:
                        # Build the vector search index
                        self._build_vector_search_index()
                except Exception as e:
                    logger.error(f"Failed to initialize vector search: {e}")
                    self.model = None
                    self.course_embeddings = None
                    self.course_ids_for_embeddings = []
                    self.embedding_index = None
            else:
                logger.warning("Skipping vector search index building due to missing dependencies")
                
            # Build BM25 index for keyword search if available
            if BM25_AVAILABLE and NLTK_AVAILABLE:
                logger.info("Building BM25 indices")
                self._build_bm25_index()
            else:
                logger.warning("Skipping BM25 index building due to missing dependencies")
                    
        except Exception as e:
            logger.error(f"Error building indexes: {str(e)}")
            # Make sure we have some fallback capabilities even if indexing fails
            self.model = None
            self.course_embeddings = None
            self.course_ids_for_embeddings = []
            self.embedding_index = None
            self.bm25_index = None
            self.tokenized_corpus = []
            self.course_ids_for_bm25 = []
    
    def _load_embedding_model(self):
        """Load the sentence transformer model for embeddings"""
        try:
            # Use a good all-purpose embedding model
            return SentenceTransformer('all-MiniLM-L6-v2')
        except Exception as e:
            logger.error(f"Error loading embedding model: {e}")
            # Fallback to a simpler model that might be already cached
            try:
                return SentenceTransformer('paraphrase-MiniLM-L3-v2')
            except Exception as e2:
                logger.error(f"Error loading fallback embedding model: {e2}")
                return None
    
    def _build_vector_search_index(self):
        """Build the vector search index for semantic search with better error handling"""
        if not self.model:
            logger.error("No embedding model available, skipping vector search index")
            return
                
        try:
            # Prepare course texts for embedding
            course_texts = []
            self.course_ids_for_embeddings = []
            
            for course_id, course in self.course_dict.items():
                # Combine relevant fields for embedding
                text_parts = []
                
                # Add class name
                if 'class_name' in course and isinstance(course['class_name'], str):
                    text_parts.append(course['class_name'])
                
                # Add class tag
                if 'class_tag' in course and isinstance(course['class_tag'], str):
                    text_parts.append(course['class_tag'])
                
                # Add description
                if 'description' in course and isinstance(course['description'], str):
                    text_parts.append(course['description'])
                
                # Add requirements
                if 'course_requirements' in course and isinstance(course['course_requirements'], str):
                    text_parts.append(f"Requirements: {course['course_requirements']}")
                
                # Add instructor
                if 'instructors' in course and isinstance(course['instructors'], str):
                    text_parts.append(f"Instructor: {course['instructors']}")
                
                # Add comments from Q reports
                if 'comments' in course and isinstance(course['comments'], str):
                    text_parts.append(f"Student comments: {course['comments']}")
                
                # Skip if no text to embed
                if not text_parts:
                    continue
                
                course_text = " ".join(text_parts)
                course_texts.append(course_text)
                self.course_ids_for_embeddings.append(course_id)
            
            # Generate embeddings if we have texts
            if len(course_texts) > 0:
                logger.info(f"Generating embeddings for {len(course_texts)} courses...")
                self.course_embeddings = self.model.encode(course_texts, show_progress_bar=True)
                
                # Check if embeddings were generated successfully
                if self.course_embeddings is None or len(self.course_embeddings) == 0:
                    logger.error("Failed to generate embeddings")
                    raise ValueError("Embedding generation failed")
                    
                # Build FAISS index for fast similarity search
                dimension = self.course_embeddings.shape[1]
                self.embedding_index = faiss.IndexFlatL2(dimension)
                self.embedding_index.add(self.course_embeddings)
                logger.info(f"Built FAISS index with {len(course_texts)} embeddings")
                
                # Cache the embeddings
                try:
                    os.makedirs(self.cache_dir, exist_ok=True)
                    with open(os.path.join(self.cache_dir, "course_embeddings.pkl"), 'wb') as f:
                        pickle.dump({
                            'embeddings': self.course_embeddings,
                            'ids': self.course_ids_for_embeddings
                        }, f)
                    logger.info("Cached course embeddings")
                except Exception as e:
                    logger.error(f"Error caching embeddings: {e}")
            else:
                logger.warning("No courses with text to embed")
                
        except Exception as e:
            logger.error(f"Error building vector search index: {e}")
            # Initialize empty structures to avoid errors elsewhere
            self.course_embeddings = None
            self.course_ids_for_embeddings = []
            self.embedding_index = None
    def get_course_workload(self, course_id=None, course_code=None):
        """Directly retrieve course workload data from q_reports"""
        if course_id is None and course_code is not None:
            # Try to get course_id from code
            course = self.get_course_by_code(course_code)
            if course:
                course_id = course.get('course_id')
        
        if course_id is None:
            return None
        
        # Convert to int if it's not already
        try:
            course_id = int(course_id)
        except (ValueError, TypeError):
            return None
        
        # Direct lookup in q_reports_df
        if hasattr(self, 'q_reports_df'):
            q_report = self.q_reports_df[self.q_reports_df['course_id'] == course_id]
            if not q_report.empty and 'mean_hours' in q_report.columns:
                hours_val = q_report['mean_hours'].iloc[0]
                if not pd.isna(hours_val):
                    return hours_val
        
        # Fall back to course_dict if q_reports lookup failed
        if course_id in self.course_dict and 'mean_hours' in self.course_dict[course_id]:
            hours_val = self.course_dict[course_id].get('mean_hours')
            if hours_val is not None and not pd.isna(hours_val):
                return hours_val
        
        return None

    def _build_bm25_index(self):
        """Build BM25 index for keyword search with error handling"""
        try:
            # Prepare corpus for BM25
            self.tokenized_corpus = []
            self.course_ids_for_bm25 = []
            
            for course_id, course in self.course_dict.items():
                # Combine relevant fields for text search
                text_parts = []
                
                # Add class name
                if 'class_name' in course and isinstance(course['class_name'], str):
                    text_parts.append(course['class_name'])
                
                # Add class tag
                if 'class_tag' in course and isinstance(course['class_tag'], str):
                    text_parts.append(course['class_tag'])
                
                # Add description
                if 'description' in course and isinstance(course['description'], str):
                    text_parts.append(course['description'])
                
                # Add requirements
                if 'course_requirements' in course and isinstance(course['course_requirements'], str):
                    text_parts.append(course['course_requirements'])
                
                # Add student comments
                if 'comments' in course and isinstance(course['comments'], str):
                    text_parts.append(course['comments'])
                
                # Skip if no text
                if not text_parts:
                    continue
                
                # Combine and tokenize
                course_text = " ".join(text_parts).lower()
                try:
                    tokenized_text = self._tokenize_text(course_text)
                    
                    if tokenized_text:  # Only add if we got tokens
                        self.tokenized_corpus.append(tokenized_text)
                        self.course_ids_for_bm25.append(course_id)
                except Exception as e:
                    logger.warning(f"Error tokenizing course {course_id}: {e}")
            
            # Create BM25 index if we have data
            if self.tokenized_corpus:
                self.bm25_index = BM25Okapi(self.tokenized_corpus)
                logger.info(f"Built BM25 index with {len(self.tokenized_corpus)} documents")
            else:
                logger.warning("No documents in BM25 index")
                
        except Exception as e:
            logger.error(f"Error building BM25 index: {e}")
            self.bm25_index = None
            self.tokenized_corpus = []
            self.course_ids_for_bm25 = []
    
    def _tokenize_text(self, text: str) -> List[str]:
        """Tokenize text for BM25 indexing with fallback for missing NLTK"""
        if not isinstance(text, str):
            return []
            
        # Use NLTK if available
        if NLTK_AVAILABLE:
            try:
                # Tokenize
                tokens = safe_word_tokenize(text)
                
                # Remove stopwords and non-alphabetic tokens
                stop_words = set(stopwords.words('english'))
                return [token.lower() for token in tokens 
                        if token.lower() not in stop_words and token.isalpha()]
            except Exception as e:
                logger.warning(f"Error using NLTK tokenization: {e}. Falling back to basic tokenization.")
                # Fall back to basic tokenization
                
        # Basic tokenization fallback
        words = text.lower().split()
        # Simple stopwords list for fallback
        basic_stopwords = {'the', 'a', 'an', 'and', 'or', 'but', 'if', 'because', 'as', 'what',
                          'when', 'where', 'how', 'who', 'which', 'this', 'that', 'these', 'those',
                          'then', 'just', 'so', 'than', 'such', 'both', 'through', 'about', 'for',
                          'is', 'of', 'while', 'during', 'to', 'from', 'in', 'on', 'at', 'by'}
        return [word for word in words if word.isalpha() and word not in basic_stopwords]
    
    def get_course_by_id(self, course_id: int) -> Optional[Dict]:
        """Get course by ID"""
        return self.course_dict.get(course_id)
    
    def get_course_by_code(self, course_code: str) -> Optional[Dict]:
        """Get course by code (e.g., 'MATH 136')"""
        course_id = self.course_by_code.get(course_code)
        if course_id:
            return self.get_course_by_id(course_id)
        return None
    
    def get_courses_by_level(self, dept: str, level: int) -> List[Dict]:
        """Get courses by department and level (e.g., 'MATH', 130)"""
        level_key = (dept, level)
        course_ids = self.courses_by_level.get(level_key, [])
        return [self.get_course_by_id(cid) for cid in course_ids if cid in self.course_dict]
    
    def get_courses_by_level_range(self, dept: str, start_level: int, end_level: int) -> List[Dict]:
        """Get courses by department and level range (e.g., 'MATH', 130, 139)"""
        result = []
        for level in range((start_level // 10) * 10, ((end_level // 10) + 1) * 10, 10):
            level_key = (dept, level)
            course_ids = self.courses_by_level.get(level_key, [])
            for cid in course_ids:
                course = self.get_course_by_id(cid)
                if course:
                    # Extract the actual course number from the class_tag
                    match = re.search(r'([A-Za-z]+)\s*(\d+)', course.get('class_tag', ''))
                    if match and int(match.group(2)) >= start_level and int(match.group(2)) <= end_level:
                        result.append(course)
        return result
    
    def get_courses_by_term(self, term: str) -> List[Dict]:
        """Get courses by term (e.g., 'Fall 2023')"""
        # Get course IDs for the specified term
        course_ids = self.courses_by_term.get(term, [])
        
        # Return all courses that match the term, regardless of missing fields
        matched_courses = []
        for cid in course_ids:
            if cid in self.course_dict:
                course = self.get_course_by_id(cid)
                # IMPORTANT: Include ALL courses that match the term, even if they have null fields
                matched_courses.append(course)
        
        # Add extra logging to help diagnose issues
        if not matched_courses and course_ids:
            logger.info(f"Term '{term}' has {len(course_ids)} course IDs but no valid courses were found")
        elif matched_courses:
            logger.info(f"Term '{term}' found {len(matched_courses)} courses")
        
        return matched_courses
    
    def get_concentration(self, concentration: str) -> Optional[Dict]:
        """Get concentration data by name"""
        return self.concentration_dict.get(concentration)
    
    def vector_search(self, query: str, top_k: int = 20) -> List[Dict]:
        """Perform semantic vector search using the query"""
        if not (SENTENCE_TRANSFORMERS_AVAILABLE and FAISS_AVAILABLE):
            logger.warning("Vector search requested but dependencies not available")
            return []  # Return empty list if functionality not available
        
        if not hasattr(self, 'embedding_index') or self.embedding_index is None:
            logger.warning("Vector search index not built")
            return []
            
        try:
            # Generate query embedding
            query_embedding = self.model.encode([query])
            
            # Search the FAISS index
            scores, indices = self.embedding_index.search(query_embedding, top_k)
            
            # Get courses from indices
            results = []
            for i in indices[0]:
                if i < len(self.course_ids_for_embeddings):
                    course_id = self.course_ids_for_embeddings[i]
                    course = self.get_course_by_id(course_id)
                    if course:
                        results.append(course)
            
            return results
        except Exception as e:
            logger.error(f"Error in vector search: {e}")
            return []
    
    def keyword_search(self, query: str, top_k: int = 20) -> List[Dict]:
        """Perform keyword-based BM25 search using the query"""
        if not (BM25_AVAILABLE and NLTK_AVAILABLE):
            logger.warning("BM25 search requested but dependencies not available")
            return []
            
        if not hasattr(self, 'bm25_index') or self.bm25_index is None:
            logger.warning("BM25 index not built")
            return []
            
        try:
            # Tokenize query
            tokenized_query = self._tokenize_text(query.lower())
            
            if not tokenized_query:
                logger.warning("Empty tokenized query")
                return []
            
            # Get BM25 scores
            bm25_scores = self.bm25_index.get_scores(tokenized_query)
            
            # Get top_k indices
            top_indices = np.argsort(bm25_scores)[::-1][:top_k]
            
            # Get courses from indices
            results = []
            for i in top_indices:
                if i < len(self.course_ids_for_bm25):
                    course_id = self.course_ids_for_bm25[i]
                    course = self.get_course_by_id(course_id)
                    if course:
                        results.append(course)
            
            return results
        except Exception as e:
            logger.error(f"Error in keyword search: {e}")
            return []
    
    def hybrid_search(self, query: str, top_k: int = 20, alpha: float = 0.5) -> List[Dict]:
        """Perform hybrid search combining vector and keyword search with reciprocal rank fusion"""
        # Check if we have this query in cache
        cache_key = f"{query}_{top_k}_{alpha}"
        if cache_key in self.search_cache:
            return self.search_cache[cache_key]
            
        try:
            # Get results from available search methods
            semantic_results = []
            if SENTENCE_TRANSFORMERS_AVAILABLE and FAISS_AVAILABLE and hasattr(self, 'embedding_index') and self.embedding_index is not None:
                semantic_results = self.vector_search(query, top_k=top_k)
                
            keyword_results = []
            if BM25_AVAILABLE and NLTK_AVAILABLE and hasattr(self, 'bm25_index') and self.bm25_index is not None:
                keyword_results = self.keyword_search(query, top_k=top_k)
                
            # If neither search method is available, fall back to basic filtering
            if not semantic_results and not keyword_results:
                logger.warning("No search methods available, falling back to basic filtering")
                # Simple text matching fallback
                results = []
                for course_id, course in self.course_dict.items():
                    # Check if query appears in course name, tag, or description
                    query_lower = query.lower()
                    if ((course.get('class_name', '') and query_lower in course['class_name'].lower()) or
                        (course.get('class_tag', '') and query_lower in course['class_tag'].lower()) or
                        (course.get('description', '') and query_lower in course['description'].lower())):
                        results.append(course)
                
                # Sort by course code (not ideal but better than nothing)
                results.sort(key=lambda x: x.get('class_tag', ''))
                return results[:top_k]
            
            # Combine using reciprocal rank fusion
            course_ranks = {}
            
            # Process semantic search results
            for i, course in enumerate(semantic_results):
                course_id = course.get('course_id')
                if course_id:
                    course_ranks[course_id] = course_ranks.get(course_id, 0) + alpha * (1.0 / (i + 1))
            
            # Process keyword search results
            for i, course in enumerate(keyword_results):
                course_id = course.get('course_id')
                if course_id:
                    course_ranks[course_id] = course_ranks.get(course_id, 0) + (1 - alpha) * (1.0 / (i + 1))
            
            # Sort by combined score
            sorted_course_ids = sorted(course_ranks.keys(), key=lambda x: course_ranks[x], reverse=True)
            
            # Get top courses
            results = []
            for course_id in sorted_course_ids[:top_k]:
                course = self.get_course_by_id(course_id)
                if course:
                    results.append(course)
            
            # Cache the results
            self.search_cache[cache_key] = results
            
            return results
        except Exception as e:
            logger.error(f"Error in hybrid search: {e}")
            return []
    
    def semantic_filter(self, courses: List[Dict], filter_query: str, min_similarity: float = 0.5) -> List[Dict]:
        """Filter courses by semantic similarity to a filter query"""
        if not courses or not SENTENCE_TRANSFORMERS_AVAILABLE or not self.model:
            return courses
            
        try:
            # Generate filter query embedding
            filter_embedding = self.model.encode([filter_query])[0]
            
            # Filter courses based on similarity
            results = []
            for course in courses:
                # Create course text
                course_text = ""
                
                if 'class_name' in course and isinstance(course['class_name'], str):
                    course_text += course['class_name'] + " "
                
                if 'description' in course and isinstance(course['description'], str):
                    course_text += course['description'] + " "
                
                if 'comments' in course and isinstance(course['comments'], str):
                    course_text += course['comments']
                
                if not course_text:
                    continue
                
                # Compute similarity
                course_embedding = self.model.encode([course_text])[0]
                similarity = self._cosine_similarity(filter_embedding, course_embedding)
                
                if similarity >= min_similarity:
                    results.append(course)
            
            return results
        except Exception as e:
            logger.error(f"Error in semantic filter: {e}")
            return courses  # Return original courses if filtering fails
    
    def _cosine_similarity(self, vec1: np.ndarray, vec2: np.ndarray) -> float:
        """Compute cosine similarity between two vectors"""
        try:
            dot_product = np.dot(vec1, vec2)
            norm_vec1 = np.linalg.norm(vec1)
            norm_vec2 = np.linalg.norm(vec2)
            
            if norm_vec1 == 0 or norm_vec2 == 0:
                return 0
            
            return dot_product / (norm_vec1 * norm_vec2)
        except Exception as e:
            logger.error(f"Error calculating cosine similarity: {e}")
            return 0.0
    
    def search_courses(self, query: str, top_k: int = 20) -> List[Dict]:
        """Enhanced course search using hybrid retrieval"""
        return self.hybrid_search(query, top_k=top_k)
    
    def filter_courses(self, 
                      dept: Optional[str] = None,
                      level: Optional[int] = None, 
                      term: Optional[str] = None,
                      min_score: Optional[float] = None,
                      max_hours: Optional[float] = None) -> List[Dict]:
        """Filter courses by criteria with error handling"""
        try:
            results = []
            
            for course_id, course in self.course_dict.items():
                # Skip if doesn't match department
                if dept and not self._course_matches_dept(course, dept):
                    continue
                
                # Skip if doesn't match level
                if level and not self._course_matches_level(course, level):
                    continue
                
                # Skip if doesn't match term
                if term and not self._course_matches_term(course, term):
                    continue
                
                # Skip if below minimum score
                if min_score and not self._course_above_min_score(course, min_score):
                    continue
                
                # Skip if above maximum hours
                if max_hours and not self._course_below_max_hours(course, max_hours):
                    continue
                
                # Passed all filters
                results.append(course)
            
            return results
            
        except Exception as e:
            logger.error(f"Error filtering courses: {e}")
            return []
    
    def find_similar_courses(self, course_code: str, top_k: int = 5) -> List[Dict]:
        """Find courses semantically similar to a given course"""
        try:
            # Get the source course
            source_course = self.get_course_by_code(course_code)
            if not source_course:
                return []
            
            # If vector search is available, use it
            if SENTENCE_TRANSFORMERS_AVAILABLE and FAISS_AVAILABLE and self.model is not None:
                # Create course text
                course_text = ""
                
                if 'class_name' in source_course and isinstance(source_course['class_name'], str):
                    course_text += source_course['class_name'] + " "
                
                if 'description' in source_course and isinstance(source_course['description'], str):
                    course_text += source_course['description']
                
                if course_text:
                    # Use vector search to find similar courses
                    similar_courses = self.vector_search(course_text, top_k=top_k+1)
                    
                    # Remove the source course from results if present
                    similar_courses = [c for c in similar_courses if c.get('class_tag') != source_course.get('class_tag')]
                    
                    return similar_courses[:top_k]
            
            # Fallback to traditional approach if vector search is unavailable or no text is available
            match = re.search(r'([A-Za-z]+)\s*(\d+)', course_code)
            if not match:
                return []
            
            dept = match.group(1)
            num = int(match.group(2))
            
            # Get courses in same department at same level
            level = (num // 10) * 10
            level_courses = self.get_courses_by_level_range(dept, level, level + 9)
            
            # Filter out the original course
            similar_courses = [c for c in level_courses if c.get('class_tag') != source_course.get('class_tag')]
            
            # Sort by score
            def sort_key(x):
                try:
                    score_value = x.get('overall_score_course_mean')
                    if score_value is None or pd.isna(score_value):
                        return 0
                    return -float(score_value)  # Negative for descending order
                except (ValueError, TypeError):
                    return 0
            
            similar_courses.sort(key=sort_key)
            
            return similar_courses[:top_k]
            
        except Exception as e:
            logger.error(f"Error finding similar courses: {e}")
            return []
    
    def _course_matches_dept(self, course: Dict, dept: str) -> bool:
        """Check if course matches department"""
        try:
            # Check if dept is in class_tag
            if 'class_tag' in course and isinstance(course['class_tag'], str):
                return dept.upper() in course['class_tag'].upper()
            return False
        except Exception:
            return False
    
    def _course_matches_level(self, course: Dict, level: int) -> bool:
        """Check if course matches level"""
        try:
            if 'class_tag' in course and isinstance(course['class_tag'], str):
                match = re.search(r'([A-Za-z]+)\s*(\d+)', course['class_tag'])
                if match:
                    num = int(match.group(2))
                    course_level = (num // 10) * 10  # Round to nearest 10
                    return course_level == level
            return False
        except Exception:
            return False
    
    def _course_matches_term(self, course: Dict, term: str) -> bool:
        """Check if course matches term"""
        try:
            if 'term' in course and isinstance(course['term'], str):
                return term.lower() in course['term'].lower()
            return False
        except Exception:
            return False
    
    def _course_above_min_score(self, course: Dict, min_score: float) -> bool:
        """Check if course is above minimum score"""
        try:
            if 'overall_score_course_mean' in course and not pd.isna(course['overall_score_course_mean']):
                try:
                    return float(course['overall_score_course_mean']) >= min_score
                except (ValueError, TypeError):
                    return False
            return False  # If no score, don't include
        except Exception:
            return False
    
    def _course_below_max_hours(self, course: Dict, max_hours: float) -> bool:
        """Check if course is below maximum hours"""
        try:
            if 'mean_hours' in course and not pd.isna(course['mean_hours']):
                try:
                    return float(course['mean_hours']) <= max_hours
                except (ValueError, TypeError):
                    return True  # If can't convert, include by default
            return True  # If no hours data, include by default
        except Exception:
            return True