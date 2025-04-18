"""
context_builder.py - Enhanced Context Builder Module

This module builds rich context for the LLM based on course data, student profile,
query analysis, and retrieved results. It implements advanced structuring techniques
for more effective prompting with enhanced reasoning traces.
"""

from typing import Dict, List, Optional, Any
import re

class ContextBuilder:
    """Builds contextually rich prompts for the LLM with reasoning traces"""
    
    def __init__(self, query_info: Dict, course_results: Dict, recommendations: Dict, 
                 student_profile: Dict, harvard_db):
        """Initialize with query and results information"""
        self.query_info = query_info
        self.course_results = course_results
        self.recommendations = recommendations
        self.student_profile = student_profile
        self.db = harvard_db
    
    def build_context(self) -> str:
        """Build a comprehensive context for the LLM with retrieval reasoning"""
        context_sections = []
        
        # 1. Add query analysis with confidence scores
        context_sections.append(self._build_query_analysis())
        
        # 2. Add retrieval reasoning trace
        context_sections.append(self._build_retrieval_reasoning())
        
        # 3. Add specific courses section (if applicable)
        if self.course_results.get("specific_courses"):
            context_sections.append(self._build_specific_courses_section())
        
        # 4. Add recommendations section (if applicable)
        if self.recommendations.get("recommended_courses"):
            context_sections.append(self._build_recommendations_section())
        
        # 5. Add relevant courses section (if applicable)
        if self.course_results.get("relevant_courses"):
            context_sections.append(self._build_relevant_courses_section())
        
        # 6. Add verification and self-reflection
        context_sections.append(self._build_verification_section())
        
        # 7. Add student profile section
        context_sections.append(self._build_student_profile_section())
        
        # 8. Add concentration requirements if applicable
        if self.student_profile.get("concentration"):
            context_sections.append(self._build_concentration_section())
        
        # 9. Add reasoning guidelines
        context_sections.append(self._build_reasoning_guidelines())
        
        # Join all sections with double newlines
        return "\n\n".join(context_sections)
    
    def _build_query_analysis(self) -> str:
        """Build the query analysis section with confidence scores"""
        analysis = ["QUERY ANALYSIS:"]
        
        # Add the original query
        analysis.append(f"Original query: \"{self.query_info['original_query']}\"")
        
        # Add intent with confidence
        intent_map = {
            "course_recommendation": "The student is looking for course recommendations",
            "course_information": "The student is asking for information about specific courses",
            "requirements": "The student is asking about requirements",
            "general_information": "The student is asking for general information",
            "comparison": "The student is asking to compare courses",
            "schedule_planning": "The student is asking for help with schedule planning"
        }
        
        intent_str = intent_map.get(self.query_info["intent"], "Unknown intent")
        confidence = self.query_info["confidence_scores"].get("intent", 0)
        analysis.append(f"Intent: {intent_str} (confidence: {confidence:.2f})")
        
        # Add department focus with confidence
        if self.query_info["departments"]:
            confidence = self.query_info["confidence_scores"].get("departments", 0)
            analysis.append(f"Department focus: {', '.join(self.query_info['departments'])} (confidence: {confidence:.2f})")
        
        # Add course levels with confidence
        if self.query_info["course_levels"]:
            level_strs = []
            for start, end in self.query_info["course_levels"]:
                if start == end:
                    level_strs.append(f"{start}")
                else:
                    level_strs.append(f"{start}-{end}")
            
            confidence = self.query_info["confidence_scores"].get("course_levels", 0)
            analysis.append(f"Course level focus: {', '.join(level_strs)} (confidence: {confidence:.2f})")
        
        # Add specific courses with confidence
        if self.query_info["course_codes"]:
            confidence = self.query_info["confidence_scores"].get("course_codes", 0)
            analysis.append(f"Specific courses mentioned: {', '.join(self.query_info['course_codes'])} (confidence: {confidence:.2f})")
        
        # Add terms with confidence
        if self.query_info["terms"]:
            confidence = self.query_info["confidence_scores"].get("terms", 0)
            analysis.append(f"Term focus: {', '.join(self.query_info['terms'])} (confidence: {confidence:.2f})")
        
        # Add constraints with confidence
        constraints = []
        if self.query_info["constraints"].get("max_hours") is not None:
            constraints.append(f"Maximum hours: {self.query_info['constraints']['max_hours']}")
        if self.query_info["constraints"].get("min_score") is not None:
            constraints.append(f"Minimum Q score: {self.query_info['constraints']['min_score']}")
        
        if constraints:
            confidence = self.query_info["confidence_scores"].get("constraints", 0)
            analysis.append(f"Constraints: {', '.join(constraints)} (confidence: {confidence:.2f})")
        
        # Add preferences with confidence
        if self.query_info["preferences"]:
            confidence = self.query_info["confidence_scores"].get("preferences", 0)
            analysis.append(f"Preferences: {', '.join(self.query_info['preferences'])} (confidence: {confidence:.2f})")
        
        # Add implicit preferences from semantic analysis
        if self.query_info.get("implicit_preferences"):
            analysis.append(f"Implicit preferences: {', '.join(self.query_info['implicit_preferences'])}")
        
        # Add semantic aspects if available
        semantic_aspects = self.query_info.get("semantic_aspects", {})
        if any(semantic_aspects.values()):
            aspects = []
            if semantic_aspects.get("difficulty"):
                aspects.append(f"Difficulty: {semantic_aspects['difficulty']}")
            if semantic_aspects.get("interest_level"):
                aspects.append(f"Interest level: {semantic_aspects['interest_level']}")
            if semantic_aspects.get("relevance"):
                aspects.append(f"Relevance: {semantic_aspects['relevance']}")
            if semantic_aspects.get("format"):
                aspects.append(f"Format: {semantic_aspects['format']}")
            
            if aspects:
                analysis.append(f"Semantic aspects: {', '.join(aspects)}")
        
        # Add follow-up information
        if self.query_info["is_followup"]:
            confidence = self.query_info["confidence_scores"].get("is_followup", 0)
            analysis.append(f"This is a follow-up question (confidence: {confidence:.2f})")
            
            if self.query_info["referenced_courses"]:
                analysis.append(f"Referenced courses: {', '.join(self.query_info['referenced_courses'])}")
        
        # Add self-reflection insights from query processor
        if self.query_info.get("self_reflection", {}).get("missing_information"):
            analysis.append(f"Missing information: {', '.join(self.query_info['self_reflection']['missing_information'])}")
        
        if self.query_info.get("self_reflection", {}).get("ambiguities"):
            analysis.append(f"Ambiguities: {', '.join(self.query_info['self_reflection']['ambiguities'])}")
        
        if self.query_info.get("self_reflection", {}).get("verification_needed"):
            analysis.append(f"Verification needed: {', '.join(self.query_info['self_reflection']['verification_needed'])}")
        
        return "\n".join(analysis)
    
    def _build_retrieval_reasoning(self) -> str:
        """Build a section explaining the retrieval reasoning process"""
        reasoning = ["RETRIEVAL REASONING:"]
        
        # Add retrieval explanation
        if self.course_results.get("retrieval_explanation"):
            reasoning.extend(self.course_results["retrieval_explanation"])
        else:
            # Create a basic retrieval explanation if detailed one isn't available
            reasoning.append("Retrieval process:")
            
            if self.course_results.get("specific_courses"):
                reasoning.append("- Found explicitly mentioned courses")
            
            if self.course_results.get("level_courses"):
                reasoning.append("- Retrieved courses matching department and level criteria")
            
            if self.course_results.get("term_courses"):
                reasoning.append("- Filtered courses by term")
            
            if self.course_results.get("filtered_courses"):
                reasoning.append("- Applied all structured filters")
            
            if self.course_results.get("semantic_matches"):
                reasoning.append("- Performed semantic search for additional matches")
            
            if self.course_results.get("relevant_courses"):
                reasoning.append("- Ranked and selected most relevant courses")
        
        # Add recommendation explanation if available
        if self.recommendations.get("explanation"):
            reasoning.append("\nRecommendation process:")
            reasoning.extend(self.recommendations["explanation"])
        elif self.recommendations.get("recommended_courses"):
            reasoning.append("\nRecommendation process:")
            reasoning.append("- Identified candidate courses based on query criteria")
            reasoning.append("- Filtered out courses already taken by the student")
            reasoning.append("- Ranked courses based on student profile and preferences")
            reasoning.append("- Selected top recommendations, workload-friendly options, and highly-rated courses")
        
        return "\n".join(reasoning)
    
    def _build_specific_courses_section(self) -> str:
        """Build the section for specific courses with detailed information"""
        section = ["SPECIFIC COURSES:"]
        
        for course in self.course_results["specific_courses"]:
            section.append(self._format_course_detail(course))
        
        return "\n".join(section)
    
    def _build_recommendations_section(self) -> str:
        """Build the recommendations section with detailed explanations"""
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
        
        # Add alternative paths if available
        if self.recommendations.get("alternative_paths"):
            section.append("\nALTERNATIVE COURSE OPTIONS:")
            for alt in self.recommendations["alternative_paths"]:
                course = alt.get("course", {})
                formatted = self._format_course_detail(course)
                
                # Add alternative path reasoning
                formatted += f"\nAlternative to: {alt.get('instead_of', 'N/A')}"
                
                if alt.get("reason"):
                    formatted += f"\nReason: {alt.get('reason')}"
                
                if alt.get("detailed_reasons"):
                    formatted += f"\nDetails: {', '.join(alt.get('detailed_reasons'))}"
                
                section.append(formatted)
        
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
    
    def _build_verification_section(self) -> str:
        """Build the verification and self-reflection section"""
        verification_points = []
        
        # Add verification from course finder
        if self.course_results.get("verification"):
            verification_points.extend(self.course_results["verification"])
        
        # Add self-reflection from recommender
        if self.recommendations.get("self_reflection"):
            verification_points.extend(self.recommendations["self_reflection"])
        
        if verification_points:
            section = ["VERIFICATION AND SELF-REFLECTION:"]
            section.extend(verification_points)
            return "\n".join(section)
        
        return ""
    
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
    
    def _build_reasoning_guidelines(self) -> str:
        """Build guidelines for LLM reasoning about recommendations"""
        guidelines = ["RESPONSE GUIDELINES:"]
        
        guidelines.append("When formulating your response:")
        
        # Add intent-specific guidelines
        if self.query_info["intent"] == "course_recommendation":
            guidelines.append("1. Focus on providing personalized course recommendations based on the student's profile and query")
            guidelines.append("2. Start with the strongest recommendation and explain why it's suitable")
            guidelines.append("3. Consider both course ratings and workload in your recommendations")
            guidelines.append("4. Address any prerequisites or potential issues identified in the verification section")
            guidelines.append("5. If workload was a key consideration, emphasize how your recommendations align with that")
        
        elif self.query_info["intent"] == "course_information":
            guidelines.append("1. Provide detailed information about the specific courses mentioned")
            guidelines.append("2. Include key details about content, format, requirements, and student feedback")
            guidelines.append("3. Relate the course information to the student's academic background when relevant")
            guidelines.append("4. Address any specific aspects of the course the student asked about")
        
        elif self.query_info["intent"] == "requirements":
            guidelines.append("1. Focus on concentration requirements and how they relate to the student's progress")
            guidelines.append("2. Explain which courses would fulfill specific requirements")
            guidelines.append("3. Consider the student's course history when discussing remaining requirements")
            guidelines.append("4. Be precise about specific requirement categories (e.g., AB0, AB1, AB2)")
        
        else:
            guidelines.append("1. Address the student's query directly based on the most relevant information provided")
            guidelines.append("2. Consider both the explicit and implicit aspects of the student's question")
            guidelines.append("3. Provide helpful context based on the student's academic background")
        
        # Add general guidelines for all responses
        guidelines.append("\nGeneral guidelines:")
        guidelines.append("- Be specific about course codes and names (e.g., MATH 131, CS 124)")
        guidelines.append("- Explain course ratings in context (e.g., 4.2/5.0 is considered good)")
        guidelines.append("- Interpret workload hours meaningfully (e.g., 8 hours/week is moderate)")
        guidelines.append("- If there are verification concerns, acknowledge them honestly")
        guidelines.append("- When discussing prerequisites, be clear about whether the student has met them")
        
        # Add confidence-based guidelines
        low_confidence_elements = []
        if self.query_info["confidence_scores"].get("intent", 1.0) < 0.7:
            low_confidence_elements.append("query intent")
        if self.query_info["confidence_scores"].get("departments", 1.0) < 0.7 and self.query_info["departments"]:
            low_confidence_elements.append("department focus")
        if self.query_info["confidence_scores"].get("course_levels", 1.0) < 0.7 and self.query_info["course_levels"]:
            low_confidence_elements.append("course level")
        
        if low_confidence_elements:
            guidelines.append(f"\nNote: There is low confidence in the following elements: {', '.join(low_confidence_elements)}. Consider acknowledging this uncertainty in your response or asking for clarification.")
        
        return "\n".join(guidelines)
    
    def _format_course_detail(self, course: Dict) -> str:
        """Format detailed course information with enhanced structure"""
        if not course:
            return ""
        
        details = []
        
        # Basic course info (with clear formatting)
        if 'class_tag' in course and 'class_name' in course:
            details.append(f"## {course['class_tag']} - {course['class_name']}")
        
        # Create sections for organized information
        basic_info = []
        ratings_info = []
        content_info = []
        logistics_info = []
        
        # Department and subject (basic info)
        if 'department' in course and course['department']:
            basic_info.append(f"Department: {course['department']}")
        
        # Term (basic info)
        if 'term' in course and course['term']:
            basic_info.append(f"Term: {course['term']}")
        
        # Instructors (basic info)
        if 'instructors' in course and course['instructors']:
            basic_info.append(f"Instructor(s): {course['instructors']}")
        
        # Q Guide data (ratings info)
        if 'overall_score_course_mean' in course and course.get('overall_score_course_mean') is not None:
            try:
                score_value = float(course['overall_score_course_mean'])
                ratings_info.append(f"Q Score: {score_value:.2f}/5.0")
            except (ValueError, TypeError):
                ratings_info.append(f"Q Score: {course['overall_score_course_mean']}")
        
        if 'mean_hours' in course and course.get('mean_hours') is not None:
            try:
                hours_value = float(course['mean_hours'])
                ratings_info.append(f"Mean Hours: {hours_value:.1f} hours/week")
            except (ValueError, TypeError):
                ratings_info.append(f"Mean Hours: {course['mean_hours']} hours/week")
        
        # Description (content info)
        if 'description' in course and course['description']:
            desc = str(course['description'])
            if len(desc) > 300:
                desc = desc[:297] + "..."
            content_info.append(f"Description: {desc}")
        
        # Requirements (logistics info)
        if 'course_requirements' in course and course['course_requirements']:
            req = str(course['course_requirements'])
            if len(req) > 200:
                req = req[:197] + "..."
            logistics_info.append(f"Requirements: {req}")
        
        # Additional logistics
        if 'room' in course and course['room']:
            logistics_info.append(f"Location: {course['room']}")
        
        if 'days' in course and course['days']:
            logistics_info.append(f"Days: {course['days']}")
        
        if 'start_times' in course and 'end_times' in course:
            logistics_info.append(f"Time: {course.get('start_times')} - {course.get('end_times')}")
        
        # Q Guide comments (ratings info)
        if 'comments' in course and course['comments'] and course.get('comments') is not None:
            comments = str(course['comments'])
            if len(comments) > 200:
                comments = comments[:197] + "..."
            ratings_info.append(f"Student Comments: {comments}")
        
        # Add the formatted sections
        if basic_info:
            details.append("Basic Information:")
            details.extend([f"- {info}" for info in basic_info])
        
        if ratings_info:
            details.append("Ratings and Workload:")
            details.extend([f"- {info}" for info in ratings_info])
        
        if content_info:
            details.append("Course Content:")
            details.extend([f"- {info}" for info in content_info])
        
        if logistics_info:
            details.append("Logistics and Requirements:")
            details.extend([f"- {info}" for info in logistics_info])
        
        return "\n".join(details)