"""
course_recommender.py - Enhanced Course Recommendation Module

This module provides sophisticated course recommendations based on student profile,
preferences, course history, and semantic similarity. It implements advanced ranking
algorithms with explanation generation for recommendations.
"""

import pandas as pd
import re
import numpy as np
from typing import Dict, List, Optional, Tuple, Set, Any, Union
from collections import defaultdict

class CourseRecommender:
    """Recommends courses based on student profile and query information with semantic understanding"""
    
    def __init__(self, harvard_db):
        """Initialize with database interface"""
        self.db = harvard_db
        
        # Cache for recommendations to avoid redundant computations
        self.recommendation_cache = {}
        
        # Track confidence in recommendations
        self.confidence = {
            "recommended_courses": 0.0,
            "workload_friendly_courses": 0.0,
            "highly_rated_courses": 0.0,
            "reasons": 0.0
        }
    
    def get_recommendations(self, query_info: Dict, student_profile: Dict) -> Dict:
        """Get course recommendations with advanced retrieval and reasoning"""
        recommendations = {
            "recommended_courses": [],
            "workload_friendly_courses": [],
            "highly_rated_courses": [],
            "reasons": {},
            "explanation": [],
            "confidence_scores": {},
            "alternative_paths": [],
            "self_reflection": []
        }
        
        # Build explanation for recommendation process
        explanation = []
        
        # Only provide recommendations for queries with recommendation intent
        if query_info["intent"] != "course_recommendation":
            explanation.append("Query intent is not asking for course recommendations.")
            recommendations["explanation"] = explanation
            return recommendations
        
        explanation.append("Starting recommendation process based on query and student profile...")
        
        # Check if we can use a cached recommendation
        cache_key = self._generate_cache_key(query_info, student_profile)
        if cache_key in self.recommendation_cache:
            cached_rec = self.recommendation_cache[cache_key]
            explanation.append("Using cached recommendations for similar query.")
            
            # Update explanation
            cached_rec["explanation"] = explanation + cached_rec.get("explanation", [])
            
            return cached_rec
        
        # Get candidate courses based on query filters
        explanation.append("Finding candidate courses based on query criteria...")
        candidate_courses = self._get_candidate_courses(query_info, student_profile)
        
        if not candidate_courses:
            explanation.append("No candidate courses found matching the basic criteria.")
            
            # Try expanding the search with more relaxed criteria
            explanation.append("Expanding search with relaxed criteria...")
            relaxed_candidates = self._get_relaxed_candidates(query_info, student_profile)
            
            if relaxed_candidates:
                explanation.append(f"Found {len(relaxed_candidates)} courses with relaxed criteria.")
                candidate_courses = relaxed_candidates
            else:
                explanation.append("Still no candidates found even with relaxed criteria.")
                recommendations["explanation"] = explanation
                recommendations["self_reflection"].append("No courses found matching the criteria")
                return recommendations
        else:
            explanation.append(f"Found {len(candidate_courses)} candidate courses.")
        
        # Filter out courses the student has already taken
        taken_course_codes = self._extract_taken_course_codes(student_profile)
        candidate_courses = [
            course for course in candidate_courses
            if course.get('class_tag') not in taken_course_codes
        ]
        
        if not candidate_courses:
            explanation.append("All candidate courses have already been taken by the student.")
            recommendations["explanation"] = explanation
            recommendations["self_reflection"].append("Student has already taken all courses matching the criteria")
            return recommendations
        
        explanation.append(f"After filtering out courses already taken, {len(candidate_courses)} candidates remain.")
        
        # Apply specialized ranking for recommendations
        explanation.append("Ranking courses based on student profile and preferences...")
        ranked_courses, confidence_score = self._rank_courses(candidate_courses, query_info, student_profile)
        
        # Store confidence
        self.confidence["recommended_courses"] = confidence_score
        
        # Store recommendations
        recommendations["recommended_courses"] = ranked_courses[:5]  # Top 5 overall
        
        if ranked_courses:
            explanation.append(f"Successfully ranked courses. Top recommendation: {ranked_courses[0].get('class_tag', 'Unknown')} - {ranked_courses[0].get('class_name', 'Unknown')}")
        else:
            explanation.append("Failed to rank courses appropriately.")
        
        # Get workload-friendly courses
        explanation.append("Identifying courses with manageable workload...")
        workload_friendly = sorted(
            [c for c in candidate_courses if c.get('mean_hours') is not None and not pd.isna(c.get('mean_hours'))],
            key=lambda x: self._safe_float(x.get('mean_hours', float('inf')))
        )
        
        recommendations["workload_friendly_courses"] = workload_friendly[:3]  # Top 3 by workload
        self.confidence["workload_friendly_courses"] = 0.9 if workload_friendly else 0.0
        
        if workload_friendly:
            explanation.append(f"Found {len(workload_friendly[:3])} courses with manageable workload.")
        else:
            explanation.append("No courses with workload information available.")
        
        # Get highly-rated courses
        explanation.append("Identifying highly-rated courses...")
        highly_rated = sorted(
            [c for c in candidate_courses if c.get('overall_score_course_mean') is not None and not pd.isna(c.get('overall_score_course_mean'))],
            key=lambda x: self._safe_float(x.get('overall_score_course_mean', 0)),
            reverse=True
        )
        
        recommendations["highly_rated_courses"] = highly_rated[:3]  # Top 3 by rating
        self.confidence["highly_rated_courses"] = 0.9 if highly_rated else 0.0
        
        if highly_rated:
            explanation.append(f"Found {len(highly_rated[:3])} highly-rated courses.")
        else:
            explanation.append("No courses with rating information available.")
        
        # Generate reasons for recommendations
        explanation.append("Generating explanations for recommendations...")
        recommendations["reasons"] = self._generate_recommendation_reasons(
            recommendations["recommended_courses"],
            query_info,
            student_profile
        )
        
        self.confidence["reasons"] = 0.85 if recommendations["reasons"] else 0.0
        
        # Find alternative paths (other courses that could be taken)
        explanation.append("Identifying alternative course paths...")
        alternatives = self._find_alternative_paths(query_info, student_profile, ranked_courses[:3])
        recommendations["alternative_paths"] = alternatives
        
        if alternatives:
            explanation.append(f"Found {len(alternatives)} alternative course paths.")
        else:
            explanation.append("No alternative course paths identified.")
        
        # Perform self-reflection on recommendations
        explanation.append("Performing self-reflection on recommendations...")
        self_reflection = self._perform_self_reflection(recommendations, query_info, student_profile)
        recommendations["self_reflection"] = self_reflection
        
        # Store confidence scores
        recommendations["confidence_scores"] = dict(self.confidence)
        
        # Save full explanation
        recommendations["explanation"] = explanation
        
        # Cache the recommendations
        self.recommendation_cache[cache_key] = recommendations
        
        return recommendations
    
    def _generate_cache_key(self, query_info: Dict, student_profile: Dict) -> str:
        """Generate a cache key for this recommendation request"""
        # Combine key elements from the query
        key_parts = []
        
        # Add departments
        if query_info["departments"]:
            key_parts.append(f"dept:{','.join(sorted(query_info['departments']))}")
        
        # Add levels
        if query_info["course_levels"]:
            level_strs = []
            for start, end in sorted(query_info["course_levels"]):
                level_strs.append(f"{start}-{end}")
            key_parts.append(f"level:{','.join(level_strs)}")
        
        # Add terms
        if query_info["terms"]:
            key_parts.append(f"term:{','.join(sorted(query_info['terms']))}")
        
        # Add constraints
        constraints = []
        if query_info["constraints"].get("max_hours") is not None:
            constraints.append(f"maxhrs:{query_info['constraints']['max_hours']}")
        if query_info["constraints"].get("min_score") is not None:
            constraints.append(f"minscore:{query_info['constraints']['min_score']}")
        if constraints:
            key_parts.append(f"constraints:{','.join(constraints)}")
        
        # Add preferences
        if query_info["preferences"]:
            key_parts.append(f"prefs:{','.join(sorted(query_info['preferences']))}")
        
        # Add student concentration
        if student_profile.get("concentration"):
            key_parts.append(f"conc:{student_profile['concentration']}")
        
        # Add taken courses count (not the specific courses, just the count)
        taken_count = len(student_profile.get("courses_taken", []))
        key_parts.append(f"taken:{taken_count}")
        
        # Join all parts with a separator
        return ";".join(key_parts)
    
    def _get_candidate_courses(self, query_info: Dict, student_profile: Dict) -> List[Dict]:
        """Get candidate courses based on query criteria with multiple retrieval paths"""
        candidate_courses = []
        
        # Track retrieval paths for debugging
        retrieval_paths = []
        
        # PRIMARY PATH: If departments and course levels are specified, use those
        if query_info["departments"] and query_info["course_levels"]:
            retrieval_paths.append("Using explicit departments and course levels")
            for dept in query_info["departments"]:
                for level_range in query_info["course_levels"]:
                    start_level, end_level = level_range
                    level_courses = self.db.get_courses_by_level_range(dept, start_level, end_level)
                    candidate_courses.extend(level_courses)
        
        # SECONDARY PATH: If only course levels are specified, try using student's concentration
        elif query_info["course_levels"] and not query_info["departments"]:
            if student_profile["concentration"]:
                retrieval_paths.append("Using course levels with student concentration")
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
            retrieval_paths.append("Filtering by term")
            term_filtered = []
            for course in candidate_courses:
                for term in query_info["terms"]:
                    if 'term' in course and isinstance(course['term'], str) and term.lower() in course['term'].lower():
                        term_filtered.append(course)
                        break
            candidate_courses = term_filtered if term_filtered else candidate_courses
        
        # Apply constraints
        constraints_applied = False
        max_hours = query_info["constraints"].get("max_hours")
        min_score = query_info["constraints"].get("min_score")
        
        if max_hours is not None:
            retrieval_paths.append(f"Filtering by max hours: {max_hours}")
            constraints_applied = True
            candidate_courses = [
                course for course in candidate_courses
                if not course.get('mean_hours') or pd.isna(course.get('mean_hours')) or self._safe_float(course.get('mean_hours')) <= max_hours
            ]
        
        if min_score is not None:
            retrieval_paths.append(f"Filtering by min score: {min_score}")
            constraints_applied = True
            candidate_courses = [
                course for course in candidate_courses
                if not course.get('overall_score_course_mean') or pd.isna(course.get('overall_score_course_mean')) or self._safe_float(course.get('overall_score_course_mean')) >= min_score
            ]
        
        # Remove duplicates while preserving order
        seen = set()
        candidate_courses = [
            course for course in candidate_courses
            if not (course.get('course_id') in seen or seen.add(course.get('course_id')))
        ]
        
        return candidate_courses
    
    def _get_relaxed_candidates(self, query_info: Dict, student_profile: Dict) -> List[Dict]:
        """Get candidate courses with relaxed criteria when strict criteria yield no results"""
        relaxed_candidates = []
        
        # Copy the query info to relax constraints
        relaxed_query = query_info.copy()
        
        # First, try relaxing max_hours and min_score constraints
        if relaxed_query["constraints"].get("max_hours") is not None:
            # Increase max hours by 50%
            relaxed_query["constraints"]["max_hours"] = relaxed_query["constraints"]["max_hours"] * 1.5
        
        if relaxed_query["constraints"].get("min_score") is not None:
            # Decrease min score by 20%
            relaxed_query["constraints"]["min_score"] = max(3.0, relaxed_query["constraints"]["min_score"] * 0.8)
        
        # Try with relaxed constraints
        relaxed_candidates = self._get_candidate_courses(relaxed_query, student_profile)
        
        # If still no results, try without constraints
        if not relaxed_candidates:
            no_constraint_query = relaxed_query.copy()
            no_constraint_query["constraints"] = {}
            
            relaxed_candidates = self._get_candidate_courses(no_constraint_query, student_profile)
        
        # If still no results and we have course levels, try expanding the level range
        if not relaxed_candidates and relaxed_query["course_levels"]:
            expanded_levels = []
            for start, end in relaxed_query["course_levels"]:
                # Expand the range by one decade on each side
                expanded_levels.append((max(0, start - 10), end + 10))
            relaxed_query["course_levels"] = expanded_levels
            
            relaxed_candidates = self._get_candidate_courses(relaxed_query, student_profile)
        
        # If all else fails, try using semantic search if available
        if not relaxed_candidates and hasattr(self.db, 'hybrid_search'):
            original_query = query_info["original_query"]
            relaxed_candidates = self.db.hybrid_search(original_query, top_k=10)
        
        return relaxed_candidates
    
    def _rank_courses(self, courses: List[Dict], query_info: Dict, student_profile: Dict) -> Tuple[List[Dict], float]:
        """Rank courses based on query preferences and profile with confidence score"""
        if not courses:
            return [], 0.0
        
        # Create tuples of (course, score, explanation) for ranking
        scored_courses = []
        
        # Start with base confidence
        confidence = 0.8
        
        # Track score components for explanation
        score_components = defaultdict(dict)
        
        for course in courses:
            course_id = course.get('course_id')
            if not course_id:
                continue
                
            score = 0
            score_explanations = []
            
            # Boost score based on Q score (0-50 points)
            if 'overall_score_course_mean' in course and not pd.isna(course.get('overall_score_course_mean')):
                try:
                    q_score = self._safe_float(course.get('overall_score_course_mean'))
                    q_points = q_score * 10  # Scale to 0-50 points
                    score += q_points
                    score_explanations.append(f"Q Score: +{q_points:.1f}")
                    score_components[course_id]['q_score'] = q_points
                except (ValueError, TypeError):
                    confidence *= 0.95  # Slight confidence reduction
            else:
                confidence *= 0.9  # More significant reduction for missing Q score
            
            # Adjust score based on workload preference
            if "easy" in query_info["preferences"]:
                if 'mean_hours' in course and not pd.isna(course.get('mean_hours')):
                    try:
                        hours = self._safe_float(course.get('mean_hours'))
                        # Lower hours = higher score (max 30 points)
                        workload_points = max(0, 30 - hours)
                        score += workload_points
                        score_explanations.append(f"Light Workload: +{workload_points:.1f}")
                        score_components[course_id]['workload'] = workload_points
                    except (ValueError, TypeError):
                        confidence *= 0.95
            elif "hard" in query_info["preferences"]:
                if 'mean_hours' in course and not pd.isna(course.get('mean_hours')):
                    try:
                        hours = self._safe_float(course.get('mean_hours'))
                        # Higher hours = higher score (max 30 points)
                        workload_points = min(30, hours)
                        score += workload_points
                        score_explanations.append(f"Challenge Level: +{workload_points:.1f}")
                        score_components[course_id]['workload'] = workload_points
                    except (ValueError, TypeError):
                        confidence *= 0.95
            else:
                # Balanced approach - prefer moderate workload (8-12 hours)
                if 'mean_hours' in course and not pd.isna(course.get('mean_hours')):
                    try:
                        hours = self._safe_float(course.get('mean_hours'))
                        # Score peaks at 10 hours (max 20 points)
                        workload_points = max(0, 20 - abs(10 - hours) * 2)
                        score += workload_points
                        score_explanations.append(f"Balanced Workload: +{workload_points:.1f}")
                        score_components[course_id]['workload'] = workload_points
                    except (ValueError, TypeError):
                        confidence *= 0.95
            
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
                    score_explanations.append("In Concentration: +10")
                    score_components[course_id]['concentration_match'] = 10
            
            # Boost for semantic aspects if available
            semantic_aspects = query_info.get("semantic_aspects", {})
            
            # Match difficulty preference
            if semantic_aspects.get("difficulty"):
                difficulty_pref = semantic_aspects["difficulty"]
                if 'mean_hours' in course and not pd.isna(course.get('mean_hours')):
                    try:
                        hours = self._safe_float(course.get('mean_hours'))
                        
                        difficulty_match = 0
                        if difficulty_pref == "easy" and hours < 10:
                            difficulty_match = 15
                        elif difficulty_pref == "moderate" and 8 <= hours <= 15:
                            difficulty_match = 15
                        elif difficulty_pref == "hard" and hours > 15:
                            difficulty_match = 15
                        
                        score += difficulty_match
                        if difficulty_match > 0:
                            score_explanations.append(f"Difficulty Match: +{difficulty_match}")
                            score_components[course_id]['difficulty_match'] = difficulty_match
                    except (ValueError, TypeError):
                        pass
            
            # Match format preference
            if semantic_aspects.get("format") and 'description' in course:
                format_pref = semantic_aspects["format"]
                desc = course.get('description', '').lower()
                
                format_match = 0
                if format_pref == "lecture" and ('lecture' in desc or 'lectures' in desc):
                    format_match = 10
                elif format_pref == "seminar" and ('seminar' in desc or 'discussion' in desc):
                    format_match = 10
                elif format_pref == "project-based" and ('project' in desc or 'lab' in desc or 'hands-on' in desc):
                    format_match = 10
                
                score += format_match
                if format_match > 0:
                    score_explanations.append(f"Format Match: +{format_match}")
                    score_components[course_id]['format_match'] = format_match
            
            # Semantic matching for interest-based preferences
            interest_prefs = [p for p in query_info["preferences"] if p.startswith("interest:")]
            if interest_prefs and hasattr(self.db, 'model'):
                # This implementation depends on the availability of semantic search
                try:
                    interest_bonus = 0
                    for pref in interest_prefs:
                        interest = pref.split(":", 1)[1]
                        if 'description' in course and interest.lower() in course.get('description', '').lower():
                            interest_bonus += 15
                    
                    if interest_bonus > 0:
                        score += interest_bonus
                        score_explanations.append(f"Interest Match: +{interest_bonus}")
                        score_components[course_id]['interest_match'] = interest_bonus
                except Exception:
                    confidence *= 0.95  # Reduce confidence if there's an error
            
            # Store the score, explanations, and course
            scored_courses.append((course, score, score_explanations))
        
        # Sort by score (descending)
        scored_courses.sort(key=lambda x: x[1], reverse=True)
        
        # Adjust confidence based on score distribution
        if scored_courses:
            # Check if there's a clear separation between top scores
            scores = [score for _, score, _ in scored_courses]
            if len(scores) >= 2:
                top_score_diff = scores[0] - scores[1]
                if top_score_diff > 20:
                    confidence = min(1.0, confidence + 0.1)  # Increase confidence for clear winner
                elif top_score_diff < 5 and len(scores) >= 3 and (scores[1] - scores[2] < 5):
                    confidence *= 0.9  # Reduce confidence for unclear distinctions
        
        # Return sorted courses and confidence
        ranked_courses = [course for course, _, _ in scored_courses]
        return ranked_courses, confidence
    
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
        """Generate detailed reasons for each recommended course"""
        reasons = {}
        
        for course in recommended_courses:
            course_tag = course.get('class_tag', '')
            if not course_tag:
                continue
                
            reason = []
            
            # Add rating-based reason
            if 'overall_score_course_mean' in course and not pd.isna(course.get('overall_score_course_mean')):
                try:
                    score = self._safe_float(course.get('overall_score_course_mean'))
                    if score >= 4.5:
                        reason.append(f"Highly rated (Q Score: {score:.2f}/5.0)")
                    elif score >= 4.0:
                        reason.append(f"Well-rated (Q Score: {score:.2f}/5.0)")
                    else:
                        reason.append(f"Q Score: {score:.2f}/5.0")
                except (ValueError, TypeError):
                    pass
            
            # Add workload-based reason
            if 'mean_hours' in course and not pd.isna(course.get('mean_hours')):
                try:
                    hours = self._safe_float(course.get('mean_hours'))
                    if "easy" in query_info["preferences"] and hours < 10:
                        reason.append(f"Light workload ({hours:.1f} hours/week)")
                    elif "hard" in query_info["preferences"] and hours > 15:
                        reason.append(f"Challenging workload ({hours:.1f} hours/week)")
                    elif hours < 8:
                        reason.append(f"Light workload ({hours:.1f} hours/week)")
                    elif hours < 12:
                        reason.append(f"Moderate workload ({hours:.1f} hours/week)")
                    else:
                        reason.append(f"Substantial workload ({hours:.1f} hours/week)")
                except (ValueError, TypeError):
                    pass
            
            # Add term-based reason
            if query_info["terms"] and 'term' in course and course['term']:
                for term in query_info["terms"]:
                    if term.lower() in course['term'].lower():
                        reason.append(f"Offered in {course['term']}")
                        break
            elif 'term' in course and course['term']:
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
                if 'course_requirements' in course and course['course_requirements']:
                    prereq_str = str(course['course_requirements'])
                    taken_courses = student_profile.get("courses_taken", [])
                    
                    # Simple check if any taken course is mentioned in prerequisites
                    prereq_met = False
                    for taken in taken_courses:
                        if taken.upper() in prereq_str.upper():
                            prereq_met = True
                            reason.append(f"Prerequisites satisfied by {taken}")
                            break
                    
                    if not prereq_met and 'prerequisite' in prereq_str.lower():
                        reason.append(f"Note: Has prerequisites")
            
            # Add semantic match reason
            for pref in query_info["preferences"]:
                if pref.startswith("interest:"):
                    interest = pref.split(":", 1)[1]
                    if 'description' in course and interest.lower() in course.get('description', '').lower():
                        reason.append(f"Covers your interest in {interest}")
            
            # Add student comments if available
            if 'comments' in course and not pd.isna(course.get('comments')):
                comments = str(course.get('comments'))
                if len(comments) > 100:
                    # Extract positive sentiment phrases
                    positive_phrases = []
                    positive_indicators = ["great", "excellent", "amazing", "good", "best", "helpful", "enjoyed", "recommended"]
                    
                    for indicator in positive_indicators:
                        pattern = rf'[^.!?]*\b{indicator}\b[^.!?]*[.!?]'
                        matches = re.findall(pattern, comments, re.IGNORECASE)
                        positive_phrases.extend(matches[:1])  # Get just the first match per indicator
                    
                    if positive_phrases:
                        reason.append(f"Student comment: \"{positive_phrases[0].strip()}\"")
            
            # Store the reasons
            reasons[course_tag] = reason
        
        return reasons
    
    def _find_alternative_paths(self, query_info: Dict, student_profile: Dict, top_courses: List[Dict]) -> List[Dict]:
        """Find alternative course paths that satisfy similar requirements"""
        alternatives = []
        
        if not top_courses:
            return alternatives
        
        # Only proceed if we have semantic search capabilities
        if not hasattr(self.db, 'find_similar_courses'):
            return alternatives
        
        # Get similar courses for each top recommendation
        seen_courses = set()
        for course in top_courses:
            if 'class_tag' not in course:
                continue
                
            course_tag = course.get('class_tag')
            if course_tag in seen_courses:
                continue
                
            seen_courses.add(course_tag)
            
            # Find similar courses
            similar_courses = self.db.find_similar_courses(course_tag, top_k=3)
            
            # Filter out courses already in top recommendations
            similar_courses = [
                c for c in similar_courses 
                if c.get('class_tag') not in seen_courses
            ]
            
            # Add explanation for each alternative
            for similar in similar_courses:
                if not similar.get('class_tag'):
                    continue
                    
                similar_tag = similar.get('class_tag')
                seen_courses.add(similar_tag)
                
                alternative = {
                    'course': similar,
                    'instead_of': course_tag,
                    'reason': f"Alternative to {course_tag}"
                }
                
                # Add additional reason details
                reasons = []
                
                # Compare ratings
                if 'overall_score_course_mean' in similar and 'overall_score_course_mean' in course:
                    try:
                        similar_score = self._safe_float(similar.get('overall_score_course_mean'))
                        course_score = self._safe_float(course.get('overall_score_course_mean'))
                        
                        if similar_score > course_score:
                            reasons.append(f"Higher rating ({similar_score:.1f} vs {course_score:.1f})")
                        elif similar_score < course_score:
                            reasons.append(f"Lower rating ({similar_score:.1f} vs {course_score:.1f})")
                        else:
                            reasons.append(f"Similar rating ({similar_score:.1f})")
                    except (ValueError, TypeError):
                        pass
                
                # Compare workload
                if 'mean_hours' in similar and 'mean_hours' in course:
                    try:
                        similar_hours = self._safe_float(similar.get('mean_hours'))
                        course_hours = self._safe_float(course.get('mean_hours'))
                        
                        if similar_hours < course_hours * 0.8:
                            reasons.append(f"Lighter workload ({similar_hours:.1f} vs {course_hours:.1f} hours)")
                        elif similar_hours > course_hours * 1.2:
                            reasons.append(f"Heavier workload ({similar_hours:.1f} vs {course_hours:.1f} hours)")
                        else:
                            reasons.append(f"Similar workload ({similar_hours:.1f} hours)")
                    except (ValueError, TypeError):
                        pass
                
                # Add term comparison
                if 'term' in similar:
                    reasons.append(f"Offered in {similar.get('term')}")
                
                # Store the reasons
                if reasons:
                    alternative['detailed_reasons'] = reasons
                
                alternatives.append(alternative)
        
        return alternatives
    
    def _perform_self_reflection(self, recommendations: Dict, query_info: Dict, student_profile: Dict) -> List[str]:
        """Perform self-reflection on recommendations to identify potential issues"""
        reflections = []
        
        # Check if we have enough recommendations
        if len(recommendations["recommended_courses"]) == 0:
            reflections.append("No courses found matching the criteria")
        elif len(recommendations["recommended_courses"]) < 3:
            reflections.append("Limited number of courses match the criteria")
        
        # Check confidence in recommendations
        if self.confidence["recommended_courses"] < 0.7:
            reflections.append("Low confidence in these recommendations, may need more specific criteria")
        
        # Check for potential prerequisite issues
        for course in recommendations["recommended_courses"]:
            if 'course_requirements' in course and course['course_requirements']:
                req_str = str(course['course_requirements'])
                if 'prerequisite' in req_str.lower() or 'prereq' in req_str.lower():
                    # Check if prerequisites are in taken courses
                    prereq_likely_met = False
                    for taken in student_profile.get("courses_taken", []):
                        if taken.upper() in req_str.upper():
                            prereq_likely_met = True
                            break
                    
                    if not prereq_likely_met:
                        reflections.append(f"Warning: {course.get('class_tag', 'Course')} may have prerequisites you haven't taken")
        
        # Check if recommendations align with query intent
        if "easy" in query_info["preferences"]:
            # Check if recommended courses have low workload
            high_workload_courses = []
            for course in recommendations["recommended_courses"]:
                if 'mean_hours' in course and not pd.isna(course.get('mean_hours')):
                    try:
                        hours = self._safe_float(course.get('mean_hours'))
                        if hours > 12:  # Threshold for "easy" courses
                            high_workload_courses.append(course.get('class_tag'))
                    except (ValueError, TypeError):
                        pass
            
            if high_workload_courses:
                reflections.append(f"Note: Some recommended courses have higher workload than requested: {', '.join(high_workload_courses)}")
        
        # Check if courses are in student's concentration
        if student_profile["concentration"] and recommendations["recommended_courses"]:
            in_concentration = [
                course for course in recommendations["recommended_courses"]
                if 'department' in course and course['department'] == student_profile["concentration"]
            ]
            
            if not in_concentration:
                reflections.append(f"None of the recommendations are in your concentration ({student_profile['concentration']})")
        
        # Check for term alignment
        if query_info["terms"] and recommendations["recommended_courses"]:
            term_mismatches = []
            for course in recommendations["recommended_courses"]:
                if 'term' in course and course['term']:
                    if not any(term.lower() in course['term'].lower() for term in query_info["terms"]):
                        term_mismatches.append(course.get('class_tag'))
            
            if term_mismatches:
                reflections.append(f"Some courses may not be offered in the requested term: {', '.join(term_mismatches)}")
        
        return reflections
    
    def _safe_float(self, value: Any) -> float:
        """Safely convert a value to float, returning a default on error"""
        try:
            return float(value)
        except (ValueError, TypeError):
            return 0.0
        
    def _get_candidate_courses(self, query_info: Dict, student_profile: Dict) -> List[Dict]:
        """Get candidate courses based on query criteria with multiple retrieval paths"""
        candidate_courses = []
        
        # Track retrieval paths for debugging
        retrieval_paths = []
        
        # PRIMARY PATH: If departments and course levels are specified, use those
        if query_info["departments"] and query_info["course_levels"]:
            retrieval_paths.append("Using explicit departments and course levels")
            for dept in query_info["departments"]:
                for level_range in query_info["course_levels"]:
                    start_level, end_level = level_range
                    level_courses = self.db.get_courses_by_level_range(dept, start_level, end_level)
                    candidate_courses.extend(level_courses)
        
        # SECONDARY PATH: If only course levels are specified, try using student's concentration
        elif query_info["course_levels"] and not query_info["departments"]:
            if student_profile["concentration"]:
                retrieval_paths.append("Using course levels with student concentration")
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
        
        # TERTIARY PATH: If hybrid search is available, use it
        if not candidate_courses and hasattr(self.db, 'hybrid_search'):
            retrieval_paths.append("Using hybrid semantic search")
            # Create a search query from the original query
            semantic_query = query_info["original_query"]
            
            # Enhance with preferences
            if query_info["preferences"]:
                pref_str = " ".join(query_info["preferences"])
                semantic_query += f" {pref_str}"
            
            # Try to find semantically relevant courses
            semantic_results = self.db.hybrid_search(semantic_query, top_k=20)
            candidate_courses.extend(semantic_results)
        
        # QUATERNARY PATH: If no specific criteria, recommend based on student's profile
        if not candidate_courses and student_profile["concentration"]:
            retrieval_paths.append("Using student profile for next-level courses")
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
            retrieval_paths.append("Filtering by term")
            term_filtered = []
            for course in candidate_courses:
                for term in query_info["terms"]:
                    if 'term' in course and isinstance(course['term'], str) and term.lower() in course['term'].lower():
                        term_filtered.append(course)
                        break
            candidate_courses = term_filtered if term_filtered else candidate_courses
        
        # Apply constraints
        constraints_applied = False
        max_hours = query_info["constraints"].get("max_hours")
        min_score = query_info["constraints"].get("min_score")
        
        if max_hours is not None:
            retrieval_paths.append(f"Filtering by max hours: {max_hours}")
            constraints_applied = True
            candidate_courses = [
                course for course in candidate_courses
                if not course.get('mean_hours') or pd.isna(course.get('mean_hours')) or self._safe_float(course.get('mean_hours')) <= max_hours
            ]
        
        if min_score is not None:
            retrieval_paths.append(f"Filtering by min score: {min_score}")
            constraints_applied = True
            candidate_courses = [
                course for course in candidate_courses
                if not course.get('overall_score_course_mean') or pd.isna(course.get('overall_score_course_mean')) or self._safe_float(course.get('overall_score_course_mean')) >= min_score
            ]
        
        # Remove duplicates while preserving order
        seen = set()
        candidate_courses = [
            course for course in candidate_courses
            if not (course.get('course_id') in seen or seen.add(course.get('course_id')))
        ]
        
        return candidate_courses