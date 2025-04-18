"""
database.py - Enhanced Database Module for Harvard Course Data

This module provides a comprehensive database interface for Harvard course data, 
with fast lookups, efficient processing, and vector-based semantic search capabilities.
"""

import pandas as pd
import re
import numpy as np
from typing import Dict, List, Optional, Tuple, Set, Any, Union
from sentence_transformers import SentenceTransformer
import faiss
from sklearn.feature_extraction.text import TfidfVectorizer
from rank_bm25 import BM25Okapi
import nltk
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
import os
import pickle

# Download NLTK resources
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt', quiet=True)
try:
    nltk.data.find('corpora/stopwords')
except LookupError:
    nltk.download('stopwords', quiet=True)

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
    
    def process_q_reports(self) -> None:
        """Process Q reports and merge with course data"""
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
    
    def process_concentrations(self) -> None:
        """Process concentration data"""
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
    
    def build_indexes(self) -> None:
        """Build advanced indexes for search and retrieval"""
        # Initialize the sentence transformer model
        self.model = self._load_embedding_model()
        
        # Check if we have cached embeddings
        cache_file = os.path.join(self.cache_dir, "course_embeddings.pkl")
        if os.path.exists(cache_file):
            try:
                with open(cache_file, 'rb') as f:
                    cache_data = pickle.load(f)
                    self.course_embeddings = cache_data.get('embeddings')
                    self.course_ids_for_embeddings = cache_data.get('ids')
                print("Loaded cached embeddings")
            except Exception as e:
                print(f"Error loading cached embeddings: {e}")
                self._build_vector_search_index()
        else:
            # Build the vector search index
            self._build_vector_search_index()
        
        # Build BM25 index for keyword search
        self._build_bm25_index()
    
    def _load_embedding_model(self):
        """Load the sentence transformer model for embeddings"""
        try:
            # Use a good all-purpose embedding model
            return SentenceTransformer('all-MiniLM-L6-v2')
        except Exception as e:
            print(f"Error loading embedding model: {e}")
            # Fallback to a simpler model that might be already cached
            return SentenceTransformer('paraphrase-MiniLM-L3-v2')
    
    def _build_vector_search_index(self):
        """Build the vector search index for semantic search"""
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
        
        # Generate embeddings
        print(f"Generating embeddings for {len(course_texts)} courses...")
        self.course_embeddings = self.model.encode(course_texts)
        
        # Build FAISS index for fast similarity search
        dimension = self.course_embeddings.shape[1]
        self.embedding_index = faiss.IndexFlatL2(dimension)
        self.embedding_index.add(self.course_embeddings)
        
        # Cache the embeddings
        try:
            os.makedirs(self.cache_dir, exist_ok=True)
            with open(os.path.join(self.cache_dir, "course_embeddings.pkl"), 'wb') as f:
                pickle.dump({
                    'embeddings': self.course_embeddings,
                    'ids': self.course_ids_for_embeddings
                }, f)
            print("Cached course embeddings")
        except Exception as e:
            print(f"Error caching embeddings: {e}")
    
    def _build_bm25_index(self):
        """Build BM25 index for keyword search"""
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
            tokenized_text = self._tokenize_text(course_text)
            
            self.tokenized_corpus.append(tokenized_text)
            self.course_ids_for_bm25.append(course_id)
        
        # Create BM25 index
        self.bm25_index = BM25Okapi(self.tokenized_corpus)
    
    def _tokenize_text(self, text: str) -> List[str]:
        """Tokenize text for BM25 indexing"""
        # Tokenize
        tokens = word_tokenize(text)
        
        # Remove stopwords and non-alphabetic tokens
        stop_words = set(stopwords.words('english'))
        return [token.lower() for token in tokens 
                if token.lower() not in stop_words and token.isalpha()]
    
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
        return [self.get_course_by_id(cid) for cid in course_ids]
    
    def get_courses_by_level_range(self, dept: str, start_level: int, end_level: int) -> List[Dict]:
        """Get courses by department and level range (e.g., 'MATH', 130, 139)"""
        result = []
        for level in range(start_level, end_level + 1):
            level_key = (dept, (level // 10) * 10)  # Round to nearest 10
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
        course_ids = self.courses_by_term.get(term, [])
        return [self.get_course_by_id(cid) for cid in course_ids]
    
    def get_concentration(self, concentration: str) -> Optional[Dict]:
        """Get concentration data by name"""
        return self.concentration_dict.get(concentration)
    
    def vector_search(self, query: str, top_k: int = 20) -> List[Dict]:
        """Perform semantic vector search using the query"""
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
    
    def keyword_search(self, query: str, top_k: int = 20) -> List[Dict]:
        """Perform keyword-based BM25 search using the query"""
        # Tokenize query
        tokenized_query = self._tokenize_text(query.lower())
        
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
    
    def hybrid_search(self, query: str, top_k: int = 20, alpha: float = 0.5) -> List[Dict]:
        """Perform hybrid search combining vector and keyword search with reciprocal rank fusion"""
        # Check if we have this query in cache
        cache_key = f"{query}_{top_k}_{alpha}"
        if cache_key in self.search_cache:
            return self.search_cache[cache_key]
        
        # Get semantic search results
        semantic_results = self.vector_search(query, top_k=top_k)
        
        # Get keyword search results
        keyword_results = self.keyword_search(query, top_k=top_k)
        
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
    
    def semantic_filter(self, courses: List[Dict], filter_query: str, min_similarity: float = 0.5) -> List[Dict]:
        """Filter courses by semantic similarity to a filter query"""
        if not courses or not self.model:
            return courses
        
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
    
    def _cosine_similarity(self, vec1: np.ndarray, vec2: np.ndarray) -> float:
        """Compute cosine similarity between two vectors"""
        dot_product = np.dot(vec1, vec2)
        norm_vec1 = np.linalg.norm(vec1)
        norm_vec2 = np.linalg.norm(vec2)
        
        if norm_vec1 == 0 or norm_vec2 == 0:
            return 0
        
        return dot_product / (norm_vec1 * norm_vec2)
    
    def search_courses(self, query: str, top_k: int = 20) -> List[Dict]:
        """Enhanced course search using hybrid retrieval"""
        return self.hybrid_search(query, top_k=top_k)
    
    def filter_courses(self, 
                      dept: Optional[str] = None,
                      level: Optional[int] = None, 
                      term: Optional[str] = None,
                      min_score: Optional[float] = None,
                      max_hours: Optional[float] = None) -> List[Dict]:
        """Filter courses by criteria"""
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
    
    def find_similar_courses(self, course_code: str, top_k: int = 5) -> List[Dict]:
        """Find courses semantically similar to a given course"""
        # Get the source course
        source_course = self.get_course_by_code(course_code)
        if not source_course:
            return []
        
        # Create course text
        course_text = ""
        
        if 'class_name' in source_course and isinstance(source_course['class_name'], str):
            course_text += source_course['class_name'] + " "
        
        if 'description' in source_course and isinstance(source_course['description'], str):
            course_text += source_course['description']
        
        if not course_text:
            # Fallback to traditional approach if no text available
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
                    return 0 if not x.get('overall_score_course_mean') or pd.isna(x.get('overall_score_course_mean')) else -float(x.get('overall_score_course_mean'))
                except (ValueError, TypeError):
                    return 0
            
            similar_courses.sort(key=sort_key)
            
            return similar_courses[:top_k]
        
        # Use vector search to find similar courses
        similar_courses = self.vector_search(course_text, top_k=top_k+1)
        
        # Remove the source course from results if present
        similar_courses = [c for c in similar_courses if c.get('class_tag') != source_course.get('class_tag')]
        
        return similar_courses[:top_k]
    
    def _course_matches_dept(self, course: Dict, dept: str) -> bool:
        """Check if course matches department"""
        # Check if dept is in class_tag
        if 'class_tag' in course and isinstance(course['class_tag'], str):
            return dept.upper() in course['class_tag'].upper()
        return False
    
    def _course_matches_level(self, course: Dict, level: int) -> bool:
        """Check if course matches level"""
        if 'class_tag' in course and isinstance(course['class_tag'], str):
            match = re.search(r'([A-Za-z]+)\s*(\d+)', course['class_tag'])
            if match:
                num = int(match.group(2))
                course_level = (num // 10) * 10  # Round to nearest 10
                return course_level == level
        return False
    
    def _course_matches_term(self, course: Dict, term: str) -> bool:
        """Check if course matches term"""
        if 'term' in course and isinstance(course['term'], str):
            return term.lower() in course['term'].lower()
        return False
    
    def _course_above_min_score(self, course: Dict, min_score: float) -> bool:
        """Check if course is above minimum score"""
        if 'overall_score_course_mean' in course and not pd.isna(course['overall_score_course_mean']):
            try:
                return float(course['overall_score_course_mean']) >= min_score
            except (ValueError, TypeError):
                return False
        return False  # If no score, don't include
    
    def _course_below_max_hours(self, course: Dict, max_hours: float) -> bool:
        """Check if course is below maximum hours"""
        if 'mean_hours' in course and not pd.isna(course['mean_hours']):
            try:
                return float(course['mean_hours']) <= max_hours
            except (ValueError, TypeError):
                return True  # If can't convert, include by default
        return True  # If no hours data, include by default