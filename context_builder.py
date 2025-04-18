"""
context_builder.py - Context Builder Module

This module builds rich context for the LLM based on course data, student profile,
and query analysis.
"""

from typing import Dict, List, Optional, Any
import re

class ContextBuilder:
    """Builds context for the LLM response"""
    
    def __init__(self, query_info: Dict, course_results: Dict, recommendations: Dict, 
                 student_profile: Dict, harvard_db):
        """Initialize with query and results information"""
        self.query_info = query_info
        self.course_results = course_results
        self.recommendations = recommendations
        self.student_profile = student_profile
        self.db = harvard_db
    
    def build_context(self) -> str:
        """Build a comprehensive context for the LLM"""
        context_sections = []
        
        # 1. Add query analysis
        context_sections.append(self._build_query_analysis())
        
        # 2. Add specific courses section
        if self.course_results.get("specific_courses"):
            context_sections.append(self._build_specific_courses_section())
        
        # 3. Add recommendations section
        if self.recommendations.get("recommended_courses"):
            context_sections.append(self._build_recommendations_section())
        
        # 4. Add relevant courses section
        if self.course_results.get("relevant_courses"):
            context_sections.append(self._build_relevant_courses_section())
        
        # 5. Add student profile section
        context_sections.append(self._build_student_profile_section())
        
        # 6. Add concentration requirements if applicable
        if self.student_profile.get("concentration"):
            context_sections.append(self._build_concentration_section())
        
        # Join all sections with double newlines
        return "\n\n".join(context_sections)
    
    def _build_query_analysis(self) -> str:
        """Build the query analysis section"""
        analysis = ["QUERY ANALYSIS:"]
        
        # Add the original query
        analysis.append(f"Original query: \"{self.query_info['original_query']}\"")
        
        # Add intent
        intent_map = {
            "course_recommendation": "The student is looking for course recommendations",
            "course_information": "The student is asking for information about specific courses",
            "requirements": "The student is asking about requirements",
            "general_information": "The student is asking for general information"
        }
        
        intent_str = intent_map.get(self.query_info["intent"], "Unknown intent")
        analysis.append(f"Intent: {intent_str}")
        
        # Add department focus
        if self.query_info["departments"]:
            analysis.append(f"Department focus: {', '.join(self.query_info['departments'])}")
        
        # Add course levels
        if self.query_info["course_levels"]:
            level_strs = []
            for start, end in self.query_info["course_levels"]:
                if start == end:
                    level_strs.append(f"{start}")
                else:
                    level_strs.append(f"{start}-{end}")
            analysis.append(f"Course level focus: {', '.join(level_strs)}")
        
        # Add specific courses
        if self.query_info["course_codes"]:
            analysis.append(f"Specific courses mentioned: {', '.join(self.query_info['course_codes'])}")
        
        # Add terms
        if self.query_info["terms"]:
            analysis.append(f"Term focus: {', '.join(self.query_info['terms'])}")
        
        # Add constraints
        constraints = []
        if self.query_info["constraints"].get("max_hours") is not None:
            constraints.append(f"Maximum hours: {self.query_info['constraints']['max_hours']}")
        if self.query_info["constraints"].get("min_score") is not None:
            constraints.append(f"Minimum Q score: {self.query_info['constraints']['min_score']}")
        if constraints:
            analysis.append(f"Constraints: {', '.join(constraints)}")
        
        # Add preferences
        if self.query_info["preferences"]:
            analysis.append(f"Preferences: {', '.join(self.query_info['preferences'])}")
        
        # Add follow-up information
        if self.query_info["is_followup"]:
            analysis.append("This is a follow-up question")
            if self.query_info["referenced_courses"]:
                analysis.append(f"Referenced courses: {', '.join(self.query_info['referenced_courses'])}")
        
        return "\n".join(analysis)
    
    def _build_specific_courses_section(self) -> str:
        """Build the section for specific courses"""
        section = ["SPECIFIC COURSES:"]
        
        for course in self.course_results["specific_courses"]:
            section.append(self._format_course_detail(course))
        
        return "\n".join(section)
    
    def _build_recommendations_section(self) -> str:
        """Build the recommendations section"""
        section = ["RECOMMENDED COURSES:"]
        
        # Add top recommendations
        for course in self.recommendations["recommended_courses"]:
            course_tag = course.get('class_tag', '')
            formatted_course = self._format_course_detail(course)
            
            # Add recommendation reasons
            if course_tag in self.recommendations.get("reasons", {}):
                reasons = self.recommendations["reasons"][course_tag]
                if reasons:
                    formatted_course += f"\nRecommendation reasons: {', '.join(reasons)}"
            
            section.append(formatted_course)
        
        # Add workload-friendly courses if different from top recommendations
        workload_friendly = self.recommendations.get("workload_friendly_courses", [])
        workload_friendly_tags = [c.get('class_tag') for c in workload_friendly if 'class_tag' in c]
        top_rec_tags = [c.get('class_tag') for c in self.recommendations["recommended_courses"] if 'class_tag' in c]
        
        unique_workload_friendly = [c for c in workload_friendly if c.get('class_tag') not in top_rec_tags]
        if unique_workload_friendly:
            section.append("\nMOST MANAGEABLE WORKLOAD COURSES:")
            for course in unique_workload_friendly:
                section.append(self._format_course_detail(course))
        
        # Add highly-rated courses if different from top recommendations
        highly_rated = self.recommendations.get("highly_rated_courses", [])
        highly_rated_tags = [c.get('class_tag') for c in highly_rated if 'class_tag' in c]
        
        unique_highly_rated = [c for c in highly_rated if c.get('class_tag') not in top_rec_tags]
        if unique_highly_rated:
            section.append("\nHIGHEST RATED COURSES:")
            for course in unique_highly_rated:
                section.append(self._format_course_detail(course))
        
        return "\n".join(section)
    
    def _build_relevant_courses_section(self) -> str:
        """Build the section for relevant courses"""
        # Skip if we already have specific courses or recommendations
        if self.course_results.get("specific_courses") or self.recommendations.get("recommended_courses"):
            return ""
        
        section = ["RELEVANT COURSES:"]
        
        for course in self.course_results["relevant_courses"]:
            section.append(self._format_course_detail(course))
        
        return "\n".join(section)
    
    def _build_student_profile_section(self) -> str:
        """Build the student profile section"""
        section = ["STUDENT PROFILE:"]
        
        # Add concentration
        if self.student_profile.get("concentration"):
            section.append(f"Concentration: {self.student_profile['concentration']}")
        
        # Add courses taken
        if self.student_profile.get("courses_taken"):
            section.append(f"Courses taken: {', '.join(self.student_profile['courses_taken'])}")
        
        return "\n".join(section)
    
    def _build_concentration_section(self) -> str:
        """Build the concentration requirements section"""
        concentration = self.student_profile.get("concentration")
        if not concentration:
            return ""
        
        section = [f"CONCENTRATION REQUIREMENTS FOR {concentration}:"]
        
        # Get concentration data
        concentration_data = self.db.get_concentration(concentration)
        if concentration_data:
            # Format requirements
            for req_field in ["ab0", "ab1", "ab2"]:
                if req_field in concentration_data and concentration_data[req_field]:
                    section.append(f"{req_field.upper()}: {concentration_data[req_field]}")
        
        return "\n".join(section)
    
    def _format_course_detail(self, course: Dict) -> str:
        """Format detailed course information"""
        if not course:
            return ""
        
        details = []
        
        # Basic course info
        if 'class_tag' in course and 'class_name' in course:
            details.append(f"{course['class_tag']} - {course['class_name']}")
        
        # Department and subject
        if 'department' in course and course['department']:
            details.append(f"Department: {course['department']}")
        
        # Term
        if 'term' in course and course['term']:
            details.append(f"Term: {course['term']}")
        
        # Q Guide data
        if 'overall_score_course_mean' in course and course.get('overall_score_course_mean') is not None:
            try:
                score_value = float(course['overall_score_course_mean'])
                details.append(f"Q Score: {score_value:.2f}/5.0")
            except (ValueError, TypeError):
                details.append(f"Q Score: {course['overall_score_course_mean']}")
        
        if 'mean_hours' in course and course.get('mean_hours') is not None:
            try:
                hours_value = float(course['mean_hours'])
                details.append(f"Mean Hours: {hours_value:.1f} hours/week")
            except (ValueError, TypeError):
                details.append(f"Mean Hours: {course['mean_hours']} hours/week")
        
        # Description (truncated if too long)
        if 'description' in course and course['description']:
            desc = str(course['description'])
            if len(desc) > 300:
                desc = desc[:297] + "..."
            details.append(f"Description: {desc}")
        
        # Requirements
        if 'course_requirements' in course and course['course_requirements']:
            req = str(course['course_requirements'])
            if len(req) > 200:
                req = req[:197] + "..."
            details.append(f"Requirements: {req}")
        
        # Q Guide comments (truncated)
        if 'comments' in course and course['comments'] and course.get('comments') is not None:
            comments = str(course['comments'])
            if len(comments) > 200:
                comments = comments[:197] + "..."
            details.append(f"Student Comments: {comments}")
        
        return "\n".join(details)