"""
course_finder.py - Course Finder Module

This module handles searching and filtering courses based on query information.
It provides direct lookup of courses and advanced filtering capabilities.
"""

from typing import Dict, List, Optional, Tuple, Set, Any
import re

class CourseFinder:
    """Finds courses based on query criteria"""
    
    def __init__(self, harvard_db):
        """Initialize with database interface"""
        self.db = harvard_db
    
    def find_courses(self, query_info: Dict, student_profile: Dict) -> Dict:
        """Find courses based on query information"""
        results = {
            "specific_courses": [],  # Courses explicitly mentioned
            "level_courses": [],     # Courses matching level criteria
            "term_courses": [],      # Courses matching term criteria
            "filtered_courses": [],  # Courses matching all filters
            "relevant_courses": []   # Most relevant courses for the query
        }
        
        # 1. Look for specific courses mentioned by code
        if query_info["course_codes"]:
            for code in query_info["course_codes"]:
                course = self.db.get_course_by_code(code)
                if course:
                    results["specific_courses"].append(course)
        
        # 2. Look for courses referenced in follow-up questions
        if query_info["referenced_courses"]:
            for code in query_info["referenced_courses"]:
                course = self.db.get_course_by_code(code)
                if course:
                    if course not in results["specific_courses"]:
                        results["specific_courses"].append(course)
        
        # 3. Find courses by department and level
        if query_info["departments"] and query_info["course_levels"]:
            for dept in query_info["departments"]:
                for level_range in query_info["course_levels"]:
                    start_level, end_level = level_range
                    level_courses = self.db.get_courses_by_level_range(dept, start_level, end_level)
                    results["level_courses"].extend(level_courses)
        elif query_info["course_levels"] and not query_info["departments"]:
            # If levels specified but no departments, try with student's concentration
            if student_profile["concentration"]:
                # Map concentration to department code
                dept_map = {
                    "Mathematics": "MATH",
                    "Computer Science": "COMPSCI",
                    "Economics": "ECON",
                    "History": "HIST",
                    "English": "ENG",
                    "Chemistry": "CHEM",
                    "Physics": "PHYSICS",
                    "Psychology": "PSY",
                    "Government": "GOV",
                    "Sociology": "SOC"
                }
                
                dept = dept_map.get(student_profile["concentration"])
                if dept:
                    for level_range in query_info["course_levels"]:
                        start_level, end_level = level_range
                        level_courses = self.db.get_courses_by_level_range(dept, start_level, end_level)
                        results["level_courses"].extend(level_courses)
        
        # 4. Find courses by term
        if query_info["terms"]:
            for term in query_info["terms"]:
                term_courses = self.db.get_courses_by_term(term)
                results["term_courses"].extend(term_courses)
        
        # 5. Apply complete filtering
        filtered_courses = self._apply_all_filters(query_info, student_profile)
        results["filtered_courses"] = filtered_courses
        
        # 6. Determine the most relevant courses
        results["relevant_courses"] = self._determine_most_relevant(results, query_info)
        
        return results
    
    def _apply_all_filters(self, query_info: Dict, student_profile: Dict) -> List[Dict]:
        """Apply all filters from query information"""
        # Start with departments
        departments = query_info["departments"]
        
        # If no departments specified, try using student's concentration
        if not departments and student_profile["concentration"]:
            # Map concentration to department
            dept_map = {
                "Mathematics": "MATH",
                "Computer Science": "COMPSCI",
                "Economics": "ECON",
                "History": "HIST",
                "English": "ENG",
                "Chemistry": "CHEM",
                "Physics": "PHYSICS",
                "Psychology": "PSY",
                "Government": "GOV",
                "Sociology": "SOC"
            }
            
            dept = dept_map.get(student_profile["concentration"])
            if dept:
                departments = [dept]
        
        # Apply department filter
        filtered_courses = []
        if departments:
            for dept in departments:
                # Get all courses for this department
                dept_courses = [
                    course for course_id, course in self.db.course_dict.items()
                    if self.db._course_matches_dept(course, dept)
                ]
                filtered_courses.extend(dept_courses)
        else:
            # No department filter, use all courses
            filtered_courses = list(self.db.course_dict.values())
        
        # Apply level filter
        if query_info["course_levels"]:
            level_filtered = []
            for course in filtered_courses:
                if 'class_tag' in course and isinstance(course['class_tag'], str):
                    match = re.search(r'([A-Za-z]+)\s*(\d+)', course['class_tag'])
                    if match:
                        num = int(match.group(2))
                        for level_range in query_info["course_levels"]:
                            start_level, end_level = level_range
                            if start_level <= num <= end_level:
                                level_filtered.append(course)
                                break
            filtered_courses = level_filtered
        
        # Apply term filter
        if query_info["terms"]:
            term_filtered = []
            for course in filtered_courses:
                for term in query_info["terms"]:
                    if self.db._course_matches_term(course, term):
                        term_filtered.append(course)
                        break
            filtered_courses = term_filtered
        
        # Apply constraints
        max_hours = query_info["constraints"].get("max_hours")
        min_score = query_info["constraints"].get("min_score")
        
        if max_hours is not None:
            filtered_courses = [
                course for course in filtered_courses
                if self.db._course_below_max_hours(course, max_hours)
            ]
        
        if min_score is not None:
            filtered_courses = [
                course for course in filtered_courses
                if self.db._course_above_min_score(course, min_score)
            ]
        
        return filtered_courses
    
    def _determine_most_relevant(self, results: Dict, query_info: Dict) -> List[Dict]:
        """Determine the most relevant courses from all results"""
        # Start with specifically mentioned courses
        relevant = list(results["specific_courses"])
        
        # If no specific courses, try filtered courses
        if not relevant and results["filtered_courses"]:
            relevant = list(results["filtered_courses"])
        
        # If still no relevant courses, try level courses
        if not relevant and results["level_courses"]:
            relevant = list(results["level_courses"])
        
        # If still no relevant courses, try term courses
        if not relevant and results["term_courses"]:
            relevant = list(results["term_courses"])
        
        # Apply sorting based on preferences
        if relevant:
            # Sort by different criteria based on intent and preferences
            if "easy" in query_info["preferences"]:
                # Sort by hours (ascending) and then by score (descending)
                def sort_key(x):
                    try:
                        hours = float('inf') if not x.get('mean_hours') or x.get('mean_hours') is None else float(x.get('mean_hours'))
                        score = 0 if not x.get('overall_score_course_mean') or x.get('overall_score_course_mean') is None else -float(x.get('overall_score_course_mean'))
                        return (hours, score)
                    except (ValueError, TypeError):
                        return (float('inf'), 0)
                
                relevant.sort(key=sort_key)
            elif "hard" in query_info["preferences"]:
                # Sort by hours (descending)
                def sort_key(x):
                    try:
                        return 0 if not x.get('mean_hours') or x.get('mean_hours') is None else -float(x.get('mean_hours'))
                    except (ValueError, TypeError):
                        return 0
                
                relevant.sort(key=sort_key)
            else:
                # Default: sort by score (descending)
                def sort_key(x):
                    try:
                        return 0 if not x.get('overall_score_course_mean') or x.get('overall_score_course_mean') is None else -float(x.get('overall_score_course_mean'))
                    except (ValueError, TypeError):
                        return 0
                
                relevant.sort(key=sort_key)
        
        # Limit to top 10 for clarity
        return relevant[:10]
    
    def find_similar_courses(self, course_code: str) -> List[Dict]:
        """Find courses similar to the given course"""
        # Get the specified course
        course = self.db.get_course_by_code(course_code)
        if not course:
            return []
        
        # Extract department and number
        match = re.search(r'([A-Za-z]+)\s*(\d+)', course_code)
        if not match:
            return []
        
        dept = match.group(1)
        num = int(match.group(2))
        
        # Get courses in same department at same level
        level = (num // 10) * 10
        level_courses = self.db.get_courses_by_level_range(dept, level, level + 9)
        
        # Filter out the original course
        similar_courses = [c for c in level_courses if c.get('class_tag') != course.get('class_tag')]
        
        # Sort by score
        def sort_key(x):
            try:
                return 0 if not x.get('overall_score_course_mean') or x.get('overall_score_course_mean') is None else -float(x.get('overall_score_course_mean'))
            except (ValueError, TypeError):
                return 0
        
        similar_courses.sort(key=sort_key)
        
        return similar_courses[:5]  # Return top 5