"""
context_builder.py - Enhanced Context Builder Module

This module builds rich context for the LLM based on course data, student profile,
query analysis, and retrieved results. It implements advanced structuring techniques
for more effective prompting with enhanced reasoning traces.
"""

from typing import Dict, List, Optional, Any
import re
import pandas as pd 

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

    def _build_workload_comparison_table(self) -> Optional[str]:
        """Add explicit workload comparison table for comparison queries"""
        # For any query related to workload or comparison
        is_comparison = (self.query_info.get("intent") == "comparison" or 
                        "compare" in self.query_info.get("original_query", "").lower() or
                        "hours" in self.query_info.get("original_query", "").lower() or
                        "workload" in self.query_info.get("original_query", "").lower())
        
        if not is_comparison:
            return None
            
        courses = self.course_results.get("specific_courses", [])
        
        # For 130s level courses, find all if we're asking for them
        if "130" in self.query_info.get("original_query", "").lower():
            # Try to get all 130s math courses if needed
            math_130s = []
            for level in range(130, 140):
                level_courses = self.db.get_courses_by_level_range("MATH", level, level)
                math_130s.extend(level_courses)
            
            # Only use them if we don't already have courses or if we have very few
            if not courses or len(courses) < 2:
                courses = math_130s
        
        if len(courses) < 1:
            return None

        # Build table header
        rows = [
            "\n**Workload Comparison Table (Mean Hours per Week):**",
            "| Course | Mean Hours | Q Score |",
            "|--------|------------|---------|"
        ]
        
        # Build table data
        for c in courses:
            name = c.get("class_tag", "UNKNOWN")
            
            # DIRECT DATABASE LOOKUP for workload data to avoid any data issues
            course_id = c.get("course_id")
            
            # Try explicit workload retrieval
            hours_val = None
            if course_id:
                hours_val = self.db.get_course_workload(course_id=course_id)
            elif name:
                hours_val = self.db.get_course_workload(course_code=name)
                
            # Format hours
            if hours_val is not None and not pd.isna(hours_val):
                try:
                    hours_float = float(hours_val)
                    hours_str = f"{hours_float:.1f}"
                except (ValueError, TypeError):
                    hours_str = "N/A"
            else:
                hours_str = "N/A"
                
            # Get Q score through similar direct lookup
            qscore_val = None
            if course_id and hasattr(self.db, 'q_reports_df'):
                q_report = self.db.q_reports_df[self.db.q_reports_df['course_id'] == course_id]
                if not q_report.empty and 'overall_score_course_mean' in q_report.columns:
                    qscore_val = q_report['overall_score_course_mean'].iloc[0]
                    
            # Format Q score
            if qscore_val is not None and not pd.isna(qscore_val):
                try:
                    qscore_float = float(qscore_val)
                    qscore_str = f"{qscore_float:.2f}"
                except (ValueError, TypeError):
                    qscore_str = "N/A"
            else:
                qscore_str = "N/A"
                
            rows.append(f"| {name} | {hours_str} | {qscore_str} |")
        
        return "\n".join(rows)


    def build_course_summary(course_row):
        return (
            f"{course_row['course_code']} - {course_row['title']}\n"
            f"Professor: {course_row['professor']} | "
            f"Q Score: {course_row['q_score']} | "
            f"Workload: {course_row['mean_hours']} hrs/week | "
            f"Difficulty: {course_row['difficulty']} | "
            f"Recommendation: {course_row['would_recommend']}%\n"
            f"Student Comments: {course_row['comments']}\n"
        )

    def build_context(self) -> str:
        """Build a comprehensive context for the LLM with retrieval reasoning"""
        context_sections = []
        
        # Build workload comparison table FIRST for any comparison-related query
        if "compare" in self.query_info.get("original_query", "").lower() or "hours" in self.query_info.get("original_query", "").lower() or "workload" in self.query_info.get("original_query", "").lower():
            comparison_table = self._build_workload_comparison_table()
            if comparison_table:
                context_sections.append("IMPORTANT WORKLOAD DATA - USE THIS INFORMATION:")
                context_sections.append(comparison_table)
        
        # Add query analysis with confidence scores
        context_sections.append(self._build_query_analysis())
        
        # Add retrieval reasoning trace
        context_sections.append(self._build_retrieval_reasoning())
        
        # Add specific courses section (if applicable)
        if self.course_results.get("specific_courses"):
            context_sections.append(self._build_specific_courses_section())

        # Inject full details for referenced courses in comparison queries to ensure LLM sees key metrics
        if self.query_info.get("intent") == "comparison" and self.query_info.get("referenced_courses"):
            context_sections.append("REFERENCED COURSES FOR COMPARISON:")
            for code in self.query_info["referenced_courses"]:
                course = self.db.get_course_by_code(code)
                if course:
                    context_sections.append(self._format_course_detail(course))
        
        # Add recommendations section (if applicable)
        if self.recommendations.get("recommended_courses"):
            context_sections.append(self._build_recommendations_section())
        
        # Add relevant courses section (if applicable)
        if self.course_results.get("relevant_courses"):
            context_sections.append(self._build_relevant_courses_section())
        
        # Add verification and self-reflection
        context_sections.append(self._build_verification_section())
        
        # Add student profile section
        context_sections.append(self._build_student_profile_section())
        
        # Add concentration requirements if applicable
        if self.student_profile.get("concentration"):
            context_sections.append(self._build_concentration_section())
        
        # Add reasoning guidelines
        context_sections.append(self._build_reasoning_guidelines())
        
        # Double check for workload comparison table if it's not at the beginning
        if "compare" in self.query_info.get("original_query", "").lower() or "hours" in self.query_info.get("original_query", "").lower() or "workload" in self.query_info.get("original_query", "").lower():
            comparison_table = self._build_workload_comparison_table()
            if comparison_table:
                context_sections.append("\nREMINDER - IMPORTANT WORKLOAD DATA:")
                context_sections.append(comparison_table)
        
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
            guidelines.append("4. Be precise about specific requirement categories (e.g., AB0 (what is AB0), AB1 (what is AB1), AB2)")
        
        else:
            guidelines.append("1. Address the student's query directly based on the most relevant information provided")
            guidelines.append("2. Consider both the explicit and implicit aspects of the student's question")
            guidelines.append("3. Provide helpful context based on the student's academic background")
        
        # Add general guidelines for all responsesguidelines.append("\nGeneral guidelines:")
        guidelines.append("- If a 'Workload Comparison Table' is provided, use it to directly compare course time commitments.")
        guidelines.append("- Explicitly compare mean hours per week between courses.")
        guidelines.append("- Prioritize structured data (tables, numeric values) over vague student impressions when available.")

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
        """Format detailed course information with full Q guide context"""
        if not course:
            return ""

        from ast import literal_eval

        def safe_float(val):
            try:
                return float(val)
            except (ValueError, TypeError):
                return None

        def pct_block(prefix, fields):
            return [
                f"{label.replace('_', ' ').title()}: {course.get(field)}"
                for label, field in fields
                if course.get(field) is not None
            ]

        lines = []
        lines.append(f"## {course.get('class_tag', 'UNKNOWN')} - {course.get('class_name', course.get('course_name', ''))}")
        lines.append(f"**Instructor:** {course.get('instructors', course.get('instructor', 'N/A'))}")
        lines.append(f"**Term:** {course.get('term', 'N/A')}")
        mean_hours_val = course.get('mean_hours')
        if isinstance(mean_hours_val, (int, float)):
            lines.append(f"**Mean Hours per Week:** {mean_hours_val:.1f}")
        else:
            lines.append(f"**Mean Hours per Week:** {mean_hours_val or 'N/A'}")

        lines.append(f"**Course Link:** {course.get('link', 'N/A')}")
        # Overall Ratings
        lines.append("\n**Overall Ratings**")
        lines.extend(pct_block("Overall", [
            ("Excellent", "overall_score_excellent"),
            ("Very Good", "overall_score_very_good"),
            ("Good", "overall_score_good"),
            ("Fair", "overall_score_fair"),
            ("Unsatisfactory", "overall_score_unsatisfactory"),
            ("Course Mean", "overall_score_course_mean"),
            ("FAS Mean", "overall_score_fas_mean"),
        ]))

        # Assignment Ratings
        lines.append("\n**Assignment Ratings**")
        lines.extend(pct_block("Assignments", [
            ("Excellent", "assignments_excellent"),
            ("Very Good", "assignments_very_good"),
            ("Good", "assignments_good"),
            ("Fair", "assignments_fair"),
            ("Unsatisfactory", "assignments_unsatisfactory"),
            ("Course Mean", "assignments_course_mean"),
            ("FAS Mean", "assignments_fas_mean"),
        ]))

        # Materials Ratings
        lines.append("\n**Materials Ratings**")
        lines.extend(pct_block("Materials", [
            ("Excellent", "materials_excellent"),
            ("Very Good", "materials_very_good"),
            ("Good", "materials_good"),
            ("Fair", "materials_fair"),
            ("Unsatisfactory", "materials_unsatisfactory"),
            ("Course Mean", "materials_course_mean"),
            ("FAS Mean", "materials_fas_mean"),
        ]))

        # Feedback Ratings
        lines.append("\n**Feedback Ratings**")
        lines.extend(pct_block("Feedback", [
            ("Excellent", "feedback_excellent"),
            ("Very Good", "feedback_very_good"),
            ("Good", "feedback_good"),
            ("Fair", "feedback_fair"),
            ("Unsatisfactory", "feedback_unsatisfactory"),
            ("Course Mean", "feedback_course_mean"),
            ("FAS Mean", "feedback_fas_mean"),
        ]))

        # Section Ratings
        lines.append("\n**Section Ratings**")
        lines.extend(pct_block("Section", [
            ("Excellent", "section_excellent"),
            ("Very Good", "section_very_good"),
            ("Good", "section_good"),
            ("Fair", "section_fair"),
            ("Unsatisfactory", "section_unsatisfactory"),
            ("Course Mean", "section_course_mean"),
            ("FAS Mean", "section_fas_mean"),
        ]))

        # Description / Requirements
        if 'description' in course:
            lines.append(f"\n**Description**: {course['description']}")
        if 'course_requirements' in course:
            lines.append(f"\n**Requirements**: {course['course_requirements']}")

        # Comments
        raw_comments = course.get("comments")
        if isinstance(raw_comments, str) and raw_comments.strip() != "":
            try:
                comments_list = literal_eval(raw_comments)
                if isinstance(comments_list, list) and comments_list:
                    lines.append("\n**Student Comments:**")
                    for c in comments_list[:3]:  # Limit to 3 long comments for context
                        lines.append(f"- {c.strip()}")
            except Exception:
                lines.append(f"\n**Student Comments (Raw):** {raw_comments.strip()}")

        return "\n".join(lines)
