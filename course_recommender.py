"""
course_recommender.py - Course Recommendation Module

This module provides specialized course recommendations based on student profile,
preferences, and course history.
"""

import pandas as pd
import re
from typing import Dict, List, Optional, Tuple, Set, Any

class CourseRecommender:
    """Recommends courses based on student profile and query information"""
    
    def __init__(self, harvard_db):
        """Initialize with database interface"""
        self.db = harvard_db
    
    def get_recommendations(self, query_info: Dict, student_profile: Dict) -> Dict:
        """Get course recommendations based on query info and student profile"""
        recommendations = {
            "recommended_courses": [],
            "workload_friendly_courses": [],
            "highly_rated_courses": [],
            "reasons": {}
        }
        
        # Only provide recommendations for queries with recommendation intent
        if query_info["intent"] != "course_recommendation":
            return recommendations
        
        # Get candidate courses based on query filters
        candidate_courses = self._get_candidate_courses(query_info, student_profile)
        
        # Filter out courses the student has already taken
        taken_course_codes = self._extract_taken_course_codes(student_profile)
        candidate_courses = [
            course for course in candidate_courses
            if course.get('class_tag') not in taken_course_codes
        ]
        
        # Apply specialized ranking for recommendations
        ranked_courses = self._rank_courses(candidate_courses, query_info, student_profile)
        
        # Store recommendations
        recommendations["recommended_courses"] = ranked_courses[:5]  # Top 5 overall
        
        # Get workload-friendly courses
        workload_friendly = sorted(
            [c for c in candidate_courses if c.get('mean_hours') is not None and not pd.isna(c.get('mean_hours'))],
            key=lambda x: float(x.get('mean_hours', float('inf')))
        )
        recommendations["workload_friendly_courses"] = workload_friendly[:3]  # Top 3 by workload
        
        # Get highly-rated courses
        highly_rated = sorted(
            [c for c in candidate_courses if c.get('overall_score_course_mean') is not None and not pd.isna(c.get('overall_score_course_mean'))],
            key=lambda x: float(x.get('overall_score_course_mean', 0)),
            reverse=True
        )
        recommendations["highly_rated_courses"] = highly_rated[:3]  # Top 3 by rating
        
        # Generate reasons for recommendations
        recommendations["reasons"] = self._generate_recommendation_reasons(
            recommendations["recommended_courses"],
            query_info,
            student_profile
        )
        
        return recommendations
    
    def _get_candidate_courses(self, query_info: Dict, student_profile: Dict) -> List[Dict]:
        """Get candidate courses based on query criteria"""
        candidate_courses = []
        
        # If departments and course levels are specified, use those
        if query_info["departments"] and query_info["course_levels"]:
            for dept in query_info["departments"]:
                for level_range in query_info["course_levels"]:
                    start_level, end_level = level_range
                    level_courses = self.db.get_courses_by_level_range(dept, start_level, end_level)
                    candidate_courses.extend(level_courses)
        
        # If only course levels are specified, try using student's concentration
        elif query_info["course_levels"] and not query_info["departments"]:
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
                        candidate_courses.extend(level_courses)
        
        # If no specific criteria, recommend based on student's profile
        if not candidate_courses and student_profile["concentration"]:
            # Get next level courses in student's concentration
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
                # Determine appropriate levels based on courses taken
                taken_levels = self._get_taken_course_levels(student_profile, dept)
                
                # Recommend next level courses
                if taken_levels:
                    max_taken = max(taken_levels)
                    next_level = ((max_taken // 10) + 1) * 10  # Next decade level
                    next_courses = self.db.get_courses_by_level_range(dept, next_level, next_level + 99)
                    candidate_courses.extend(next_courses)
                else:
                    # No courses taken in this dept, recommend intro courses
                    intro_courses = self.db.get_courses_by_level_range(dept, 0, 99)
                    candidate_courses.extend(intro_courses)
        
        # Apply term filter if specified
        if query_info["terms"] and candidate_courses:
            term_filtered = []
            for course in candidate_courses:
                for term in query_info["terms"]:
                    if 'term' in course and isinstance(course['term'], str) and term.lower() in course['term'].lower():
                        term_filtered.append(course)
                        break
            candidate_courses = term_filtered if term_filtered else candidate_courses
        
        # Apply constraints
        max_hours = query_info["constraints"].get("max_hours")
        min_score = query_info["constraints"].get("min_score")
        
        if max_hours is not None:
            candidate_courses = [
                course for course in candidate_courses
                if not course.get('mean_hours') or pd.isna(course.get('mean_hours')) or float(course.get('mean_hours')) <= max_hours
            ]
        
        if min_score is not None:
            candidate_courses = [
                course for course in candidate_courses
                if not course.get('overall_score_course_mean') or pd.isna(course.get('overall_score_course_mean')) or float(course.get('overall_score_course_mean')) >= min_score
            ]
        
        return candidate_courses
    
    def _rank_courses(self, courses: List[Dict], query_info: Dict, student_profile: Dict) -> List[Dict]:
        """Rank courses based on query preferences and profile"""
        if not courses:
            return []
        
        # Create tuples of (course, score) for ranking
        scored_courses = []
        
        for course in courses:
            score = 0
            
            # Boost score based on Q score
            if 'overall_score_course_mean' in course and not pd.isna(course.get('overall_score_course_mean')):
                q_score = float(course.get('overall_score_course_mean'))
                score += q_score * 10  # Scale to 0-50 points
            
            # Adjust score based on workload preference
            if "easy" in query_info["preferences"]:
                if 'mean_hours' in course and not pd.isna(course.get('mean_hours')):
                    hours = float(course.get('mean_hours'))
                    # Lower hours = higher score (max 30 points)
                    score += max(0, 30 - hours)
            elif "hard" in query_info["preferences"]:
                if 'mean_hours' in course and not pd.isna(course.get('mean_hours')):
                    hours = float(course.get('mean_hours'))
                    # Higher hours = higher score (max 30 points)
                    score += min(30, hours)
            else:
                # Balanced approach - prefer moderate workload (8-12 hours)
                if 'mean_hours' in course and not pd.isna(course.get('mean_hours')):
                    hours = float(course.get('mean_hours'))
                    # Score peaks at 10 hours (max 20 points)
                    score += max(0, 20 - abs(10 - hours) * 2)
            
            # Boost courses that match student's concentration
            if student_profile["concentration"]:
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
                if dept and 'class_tag' in course and dept in course.get('class_tag', ''):
                    score += 10  # Boost for matching department
            
            scored_courses.append((course, score))
        
        # Sort by score (descending)
        scored_courses.sort(key=lambda x: x[1], reverse=True)
        
        # Return sorted courses
        return [course for course, _ in scored_courses]
    
    def _extract_taken_course_codes(self, student_profile: Dict) -> Set[str]:
        """Extract course codes from the courses the student has taken"""
        taken_codes = set()
        
        for course in student_profile.get("courses_taken", []):
            # Try to extract a course code
            match = re.search(r'([A-Za-z]+)\s*(\d+)', course)
            if match:
                dept = match.group(1).upper()
                num = match.group(2)
                code = f"{dept} {num}"
                taken_codes.add(code)
            else:
                # If not in standard format, just add the raw course
                taken_codes.add(course)
        
        return taken_codes
    
    def _get_taken_course_levels(self, student_profile: Dict, dept: str) -> List[int]:
        """Get the levels of courses the student has taken in a department"""
        levels = []
        
        for course in student_profile.get("courses_taken", []):
            # Look for courses in the specified department
            match = re.search(rf'({dept})\s*(\d+)', course, re.IGNORECASE)
            if match:
                num = int(match.group(2))
                levels.append(num)
        
        return levels
    
    def _generate_recommendation_reasons(self, recommended_courses: List[Dict], query_info: Dict, student_profile: Dict) -> Dict:
        """Generate reasons for each recommended course"""
        reasons = {}
        
        for course in recommended_courses:
            course_tag = course.get('class_tag', '')
            reason = []
            
            # Add rating-based reason
            if 'overall_score_course_mean' in course and not pd.isna(course.get('overall_score_course_mean')):
                score = float(course.get('overall_score_course_mean'))
                if score >= 4.5:
                    reason.append(f"Highly rated (Q Score: {score:.2f})")
                elif score >= 4.0:
                    reason.append(f"Well-rated (Q Score: {score:.2f})")
                else:
                    reason.append(f"Q Score: {score:.2f}")
            
            # Add workload-based reason
            if 'mean_hours' in course and not pd.isna(course.get('mean_hours')):
                hours = float(course.get('mean_hours'))
                if hours < 8:
                    reason.append(f"Light workload ({hours:.1f} hours/week)")
                elif hours < 12:
                    reason.append(f"Moderate workload ({hours:.1f} hours/week)")
                else:
                    reason.append(f"Heavy workload ({hours:.1f} hours/week)")
            
            # Add term-based reason
            if 'term' in course and course['term']:
                reason.append(f"Offered in {course['term']}")
            
            # Add level-based reason
            if course_tag:
                match = re.search(r'([A-Za-z]+)\s*(\d+)', course_tag)
                if match:
                    level = int(match.group(2))
                    if level < 100:
                        reason.append("Introductory level course")
                    elif 100 <= level < 200:
                        reason.append("Intermediate undergraduate course")
                    else:
                        reason.append("Advanced course")
            
            # Add reasons based on student profile
            if student_profile["concentration"]:
                if 'department' in course and course['department'] == student_profile["concentration"]:
                    reason.append(f"In your concentration ({student_profile['concentration']})")
                
                # Check if prerequisites have been taken
                if course_tag and student_profile["courses_taken"]:
                    # This is simplified; in a real system, you'd have a prereq graph
                    taken_numbers = []
                    for taken in student_profile["courses_taken"]:
                        match = re.search(r'([A-Za-z]+)\s*(\d+)', taken)
                        if match:
                            taken_numbers.append(int(match.group(2)))
                    
                    if taken_numbers:
                        match = re.search(r'([A-Za-z]+)\s*(\d+)', course_tag)
                        if match:
                            course_num = int(match.group(2))
                            if any(num < course_num for num in taken_numbers):
                                reason.append("Builds on your previous coursework")
            
            # Store the reasons
            reasons[course_tag] = reason
        
        return reasons