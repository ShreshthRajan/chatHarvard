"""
database.py - Database Module for Harvard Course Data

This module provides a comprehensive database interface for Harvard course data, 
with fast lookups and efficient processing.
"""

import pandas as pd
import re
from typing import Dict, List, Optional, Tuple, Set, Any
import numpy as np

class HarvardDatabase:
    """Database for Harvard courses, Q reports, and concentrations"""
    
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
        """Build additional indexes for faster lookups"""
        # Add any additional indexing here
        pass
    
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
    
    def search_courses(self, query: str) -> List[Dict]:
        """Search for courses by name or description"""
        query_lower = query.lower()
        results = []
        
        for course_id, course in self.course_dict.items():
            # Check name
            if 'class_name' in course and isinstance(course['class_name'], str):
                if query_lower in course['class_name'].lower():
                    results.append(course)
                    continue
            
            # Check description
            if 'description' in course and isinstance(course['description'], str):
                if query_lower in course['description'].lower():
                    results.append(course)
                    continue
        
        return results
    
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
            return float(course['overall_score_course_mean']) >= min_score
        return False  # If no score, don't include
    
    def _course_below_max_hours(self, course: Dict, max_hours: float) -> bool:
        """Check if course is below maximum hours"""
        if 'mean_hours' in course and not pd.isna(course['mean_hours']):
            return float(course['mean_hours']) <= max_hours
        return True  # If no hours data, include by default