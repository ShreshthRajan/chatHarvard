"""
course_finder.py - Enhanced Course Finder Module

This module handles searching and filtering courses based on query information
using hybrid retrieval techniques that combine structured filtering and
semantic search capabilities.
"""

import re
import numpy as np
from typing import Dict, List, Optional, Tuple, Set, Any, Union
from collections import defaultdict

class CourseFinder:
    """Finds courses based on query criteria with advanced retrieval techniques"""
    
    def __init__(self, harvard_db):
        """Initialize with database interface"""
        self.db = harvard_db
        
        # Cache for search results to avoid redundant computations
        self.search_cache = {}
        
        # Track confidence in results
        self.confidence_scores = {
            "specific_courses": 0.0,
            "level_courses": 0.0,
            "term_courses": 0.0,
            "filtered_courses": 0.0,
            "semantic_matches": 0.0,
            "relevant_courses": 0.0
        }
    
    def find_courses(self, query_info: Dict, student_profile: Dict) -> Dict:
        """Find courses based on query information using hybrid retrieval"""
        results = {
            "specific_courses": [],  # Courses explicitly mentioned
            "level_courses": [],     # Courses matching level criteria
            "term_courses": [],      # Courses matching term criteria
            "filtered_courses": [],  # Courses matching all filters
            "semantic_matches": [],  # Courses matching semantic search
            "relevant_courses": [],  # Most relevant courses for the query
            "confidence_scores": {}, # Confidence in each result set
            "retrieval_explanation": [], # Explanation of retrieval process
            "verification": []       # Verification of results against requirements
        }
        
        # Track explanations for retrieval process
        explanations = []
        
        # 1. Start with explicitly mentioned courses (highest precision)
        explanations.append("Step 1: Looking for explicitly mentioned courses...")
        specific_courses, specific_conf = self._find_specific_courses(query_info)
        results["specific_courses"] = specific_courses
        self.confidence_scores["specific_courses"] = specific_conf
        
        if specific_courses:
            explanations.append(f"Found {len(specific_courses)} explicitly mentioned courses")
        else:
            explanations.append("No explicitly mentioned courses found")
        
        # 2. Find courses by department and level (structured search)
        explanations.append("Step 2: Searching by department and course level...")
        level_courses, level_conf = self._find_courses_by_level(query_info, student_profile)
        results["level_courses"] = level_courses
        self.confidence_scores["level_courses"] = level_conf
        
        if level_courses:
            explanations.append(f"Found {len(level_courses)} courses matching department and level criteria")
        else:
            explanations.append("No courses found matching department and level criteria")
        
        # 3. Find courses by term
        explanations.append("Step 3: Filtering courses by term...")
        term_courses, term_conf = self._find_courses_by_term(query_info)
        results["term_courses"] = term_courses
        self.confidence_scores["term_courses"] = term_conf
        
        if term_courses:
            explanations.append(f"Found {len(term_courses)} courses matching term criteria")
        else:
            explanations.append("No term specified or no courses found for the specified term")
        
        # 4. Apply complete filtering with all structured constraints
        explanations.append("Step 4: Applying all structured filters...")
        filtered_courses, filter_conf = self._apply_all_filters(query_info, student_profile)
        results["filtered_courses"] = filtered_courses
        self.confidence_scores["filtered_courses"] = filter_conf
        
        if filtered_courses:
            explanations.append(f"Found {len(filtered_courses)} courses matching all structured filters")
        else:
            explanations.append("No courses found matching all structured filters")
        
        # 5. Apply semantic search for implicit criteria (if available)
        explanations.append("Step 5: Applying semantic search for implicit criteria...")
        semantic_matches, semantic_conf = self._find_semantic_matches(query_info, student_profile)
        results["semantic_matches"] = semantic_matches
        self.confidence_scores["semantic_matches"] = semantic_conf
        
        if semantic_matches:
            explanations.append(f"Found {len(semantic_matches)} courses matching semantic criteria")
        else:
            explanations.append("No additional courses found through semantic search")
        
        # 6. Determine the most relevant courses through hybrid ranking
        explanations.append("Step 6: Determining most relevant courses through hybrid ranking...")
        relevant_courses, relevant_conf = self._determine_most_relevant(results, query_info, student_profile)
        results["relevant_courses"] = relevant_courses
        self.confidence_scores["relevant_courses"] = relevant_conf
        
        if relevant_courses:
            explanations.append(f"Selected {len(relevant_courses)} most relevant courses")
        else:
            explanations.append("Could not determine relevant courses")
        
        # 7. Verify results against requirements (self-reflection)
        explanations.append("Step 7: Verifying results against requirements...")
        verification = self._verify_results(results, query_info, student_profile)
        results["verification"] = verification
        
        if verification:
            explanations.append(f"Found {len(verification)} verification notes about the results")
        
        # Store confidence scores
        results["confidence_scores"] = dict(self.confidence_scores)
        
        # Store retrieval explanation
        results["retrieval_explanation"] = explanations
        
        return results
    
    def _find_specific_courses(self, query_info: Dict) -> Tuple[List[Dict], float]:
        """Find specific courses mentioned by code or referenced in follow-up"""
        specific_courses = []
        confidence = 0.0
        
        # Look for courses explicitly mentioned by code
        if query_info["course_codes"]:
            confidence = query_info["confidence_scores"].get("course_codes", 0.8)
            
            for code in query_info["course_codes"]:
                course = self.db.get_course_by_code(code)
                
                if course:
                    # For comparison queries, ensure we have complete data including workload
                    if query_info.get("intent") == "comparison":
                        # If the course data is missing workload info, try direct database lookup
                        if 'mean_hours' not in course or course['mean_hours'] is None:
                            # Try getting q_report data directly
                            course_id = course.get('course_id')
                            if course_id and hasattr(self.db, 'q_reports_df'):
                                q_report = self.db.q_reports_df[self.db.q_reports_df['course_id'] == course_id]
                                if not q_report.empty and 'mean_hours' in q_report.columns:
                                    course['mean_hours'] = q_report['mean_hours'].iloc[0]
                    
                    specific_courses.append(course)
                else:
                    # Reduce confidence if we couldn't find a mentioned course
                    confidence *= 0.9
        
        # Look for courses referenced in follow-up questions
        if query_info["referenced_courses"]:
            ref_confidence = query_info["confidence_scores"].get("is_followup", 0.7)
            
            for code in query_info["referenced_courses"]:
                course = self.db.get_course_by_code(code)
                if course:
                    if course not in specific_courses:
                        specific_courses.append(course)
                else:
                    # Reduce confidence if we couldn't find a referenced course
                    ref_confidence *= 0.8
            
            # Combine confidences
            if not specific_courses:
                confidence = ref_confidence
            else:
                confidence = max(confidence, ref_confidence)
        
        return specific_courses, confidence
    
    def _find_courses_by_level(self, query_info: Dict, student_profile: Dict) -> Tuple[List[Dict], float]:
        """Find courses by department and level criteria"""
        level_courses = []
        confidence = 0.0
        
        # Only proceed if we have departments and levels
        if query_info["departments"] and query_info["course_levels"]:
            confidence = min(
                query_info["confidence_scores"].get("departments", 0.7),
                query_info["confidence_scores"].get("course_levels", 0.7)
            )
            
            for dept in query_info["departments"]:
                for level_range in query_info["course_levels"]:
                    start_level, end_level = level_range
                    dept_level_courses = self.db.get_courses_by_level_range(dept, start_level, end_level)
                    level_courses.extend(dept_level_courses)
                    
                    # Adjust confidence based on results
                    if not dept_level_courses:
                        confidence *= 0.9  # Reduce confidence if no courses found
        
        # If levels specified but no departments, try with student's concentration
        elif query_info["course_levels"] and not query_info["departments"]:
            confidence = query_info["confidence_scores"].get("course_levels", 0.7) * 0.8  # Lower confidence without explicit dept
            
            if student_profile["concentration"]:
                # Map concentration to department code
                dept_map = {
                    # Mathematics and Computation
                    'MATH': 'MATHEMATICS',
                    'MATHS': 'MATHEMATICS',
                    'PURE MATH': 'MATHEMATICS',
                    'STAT': 'STATISTICS',
                    'STATS': 'STATISTICS',
                    
                    # Computer Science and Engineering
                    'COMPSCI': 'COMPUTER SCIENCE',
                    'CS': 'COMPUTER SCIENCE',
                    'COMP SCI': 'COMPUTER SCIENCE',
                    'APMATH': 'APPLIED MATHEMATICS',
                    'APMTH': 'APPLIED MATHEMATICS',
                    'AM': 'APPLIED MATHEMATICS',
                    'BME': 'BIOMEDICAL ENGINEERING',
                    'EE': 'ELECTRICAL ENGINEERING',
                    'ES': 'ENGINEERING SCIENCES',
                    'ESE': 'ENVIRONMENTAL SCIENCE AND ENGINEERING',
                    'ME': 'MECHANICAL ENGINEERING',
                    
                    # Physical Sciences
                    'PHYS': 'PHYSICS',
                    'ASTRO': 'ASTROPHYSICS',
                    'EPS': 'EARTH AND PLANETARY SCIENCES',
                    
                    # Life Sciences
                    'CHEM': 'CHEMISTRY',
                    'CPB': 'CHEMICAL AND PHYSICAL BIOLOGY',
                    'HDRB': 'HUMAN DEVELOPMENTAL AND REGENERATIVE BIOLOGY',
                    'HEB': 'HUMAN EVOLUTIONARY BIOLOGY',
                    'IB': 'INTEGRATIVE BIOLOGY',
                    'MCB': 'MOLECULAR AND CELLULAR BIOLOGY',
                    'NEURO': 'NEUROSCIENCE',
                    
                    # Qualitative Social Sciences
                    'ANTHRO': 'ANTHROPOLOGY',
                    'FM': 'FOLKLORE AND MYTHOLOGY',
                    'SOC': 'SOCIOLOGY',
                    'WGS': 'WOMEN, GENDER, AND SEXUALITY',
                    
                    # Quantitative Social Sciences
                    'AAAS': 'AFRICAN AND AFRICAN AMERICAN STUDIES',
                    'ECON': 'ECONOMICS',
                    'GOV': 'GOVERNMENT',
                    'GOVT': 'GOVERNMENT',
                    'HIST-SCI': 'HISTORY AND SCIENCE',
                    'HISTSCI': 'HISTORY AND SCIENCE',
                    'PSY': 'PSYCHOLOGY',
                    'PSYCH': 'PSYCHOLOGY',
                    'SOC-STD': 'SOCIAL STUDIES',
                    'SOCSTD': 'SOCIAL STUDIES',
                    'SOC STD': 'SOCIAL STUDIES',
                    'SOCSTUDY': 'SOCIAL STUDIES',
                    
                    # History
                    'HIST': 'HISTORY',
                    'HIST-LIT': 'HISTORY AND LITERATURE',
                    'HISTLIT': 'HISTORY AND LITERATURE',
                    
                    # Languages, Literatures, and Religion
                    'COMPLIT': 'COMPARATIVE LITERATURE',
                    'EAS': 'EAST ASIAN STUDIES',
                    'ENGLISH': 'ENGLISH',
                    'ENG': 'ENGLISH',
                    'GERMANIC': 'GERMANIC LANGUAGES AND LITERATURES',
                    'GERMAN': 'GERMANIC LANGUAGES AND LITERATURES',
                    'NELC': 'NEAR EASTERN LANGUAGES AND CIVILIZATIONS',
                    'REL': 'RELIGION',
                    'RELIGION': 'RELIGION',
                    'RELIG': 'RELIGION',
                    'ROM-LANG': 'ROMANCE LANGUAGES AND LITERATURES',
                    'ROMANCE': 'ROMANCE LANGUAGES AND LITERATURES',
                    'SLAVIC': 'SLAVIC LANGUAGES AND LITERATURES',
                    
                    # Arts
                    'AFVS': 'ART, FILM, AND VISUAL STUDIES',
                    'VES': 'ART, FILM, AND VISUAL STUDIES', # old name
                    'ART': 'ART, FILM, AND VISUAL STUDIES',
                    
                    # Specific Languages and Regional Studies
                    'FRENCH': 'ROMANCE LANGUAGES AND LITERATURES',
                    'SPANISH': 'ROMANCE LANGUAGES AND LITERATURES',
                    'ITALIAN': 'ROMANCE LANGUAGES AND LITERATURES',
                    'PORTUGUESE': 'ROMANCE LANGUAGES AND LITERATURES',
                    'LATIN': 'CLASSICS',
                    'GREEK': 'CLASSICS',
                    'CLASSICS': 'CLASSICS',
                    'CHINESE': 'EAST ASIAN STUDIES',
                    'JAPANESE': 'EAST ASIAN STUDIES',
                    'KOREAN': 'EAST ASIAN STUDIES',
                    'RUSSIAN': 'SLAVIC LANGUAGES AND LITERATURES',
                    
                    # Additional common abbreviations
                    'EXPOS': 'EXPOSITORY WRITING',
                    'GEN-ED': 'GENERAL EDUCATION',
                    'GENED': 'GENERAL EDUCATION',
                }
                
                dept = dept_map.get(student_profile["concentration"])
                if dept:
                    for level_range in query_info["course_levels"]:
                        start_level, end_level = level_range
                        dept_level_courses = self.db.get_courses_by_level_range(dept, start_level, end_level)
                        level_courses.extend(dept_level_courses)
                        
                        # Adjust confidence based on results
                        if not dept_level_courses:
                            confidence *= 0.9  # Reduce confidence if no courses found
        
        return level_courses, confidence
    
    def _find_courses_by_department(self, departments: List[str], student_profile: Dict) -> Tuple[List[Dict], float]:
        """Find courses by department with better handling of interdisciplinary programs"""
        dept_courses = []
        confidence = 0.7  # Base confidence
        
        for dept in departments:
            # Check if this is a known interdisciplinary program that spans multiple departments
            if dept.upper() == "SOCIAL STUDIES":
                # For Social Studies, include courses from multiple relevant departments
                relevant_depts = ["GOV", "HIST", "SOC", "ECON", "SOCSTD", "SOC-STD"]
                for relevant_dept in relevant_depts:
                    # Get courses for this department
                    for course_id, course in self.db.course_dict.items():
                        if self._course_matches_dept(course, relevant_dept):
                            dept_courses.append(course)
            else:
                # Standard department query
                for course_id, course in self.db.course_dict.items():
                    if self._course_matches_dept(course, dept):
                        dept_courses.append(course)
        
        # If no courses found, reduce confidence
        if not dept_courses:
            confidence *= 0.8
        
        return dept_courses, confidence

    def _find_courses_by_term(self, query_info: Dict) -> Tuple[List[Dict], float]:
        """Find courses by term criteria"""
        term_courses = []
        confidence = 0.0
        
        if query_info["terms"]:
            confidence = query_info["confidence_scores"].get("terms", 0.7)
            
            for term in query_info["terms"]:
                # Direct database query to ensure ALL matching courses are included
                # This bypasses any potential filtering issues
                term_courses_batch = []
                
                # Search for the term in all courses
                for course_id, course in self.db.course_dict.items():
                    if course.get('term') and term.lower() in course.get('term', '').lower():
                        term_courses_batch.append(course)
                
                term_courses.extend(term_courses_batch)
                
                # Adjust confidence based on results
                if not term_courses_batch:
                    confidence *= 0.9  # Reduce confidence if no courses found for a term
        
        return term_courses, confidence
    
    def _apply_all_filters(self, query_info: Dict, student_profile: Dict) -> Tuple[List[Dict], float]:
        """Apply all structured filters from query information"""
        # Track overall confidence
        confidence = 0.8  # Start with default confidence
        
        # Start with departments
        departments = query_info["departments"]
        if departments:
            confidence = min(confidence, query_info["confidence_scores"].get("departments", 0.7))
        
        # If no departments specified, try using student's concentration
        if not departments and student_profile["concentration"]:
            confidence *= 0.9  # Lower confidence for implicit department
            
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
                    if self._course_matches_dept(course, dept)
                ]
                filtered_courses.extend(dept_courses)
        else:
            # No department filter, use all courses
            filtered_courses = list(self.db.course_dict.values())
            confidence *= 0.8  # Lower confidence when not filtering by department
        
        # Apply level filter
        if query_info["course_levels"]:
            level_confidence = query_info["confidence_scores"].get("course_levels", 0.7)
            confidence = min(confidence, level_confidence)
            
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
            term_confidence = query_info["confidence_scores"].get("terms", 0.7)
            confidence = min(confidence, term_confidence)
            
            term_filtered = []
            for course in filtered_courses:
                for term in query_info["terms"]:
                    if self._course_matches_term(course, term):
                        term_filtered.append(course)
                        break
            filtered_courses = term_filtered
        
        # Apply constraints
        constraints_confidence = query_info["confidence_scores"].get("constraints", 0.7)
        
        max_hours = query_info["constraints"].get("max_hours")
        min_score = query_info["constraints"].get("min_score")
        
        if max_hours is not None:
            confidence = min(confidence, constraints_confidence)
            filtered_courses = [
                course for course in filtered_courses
                if self._course_below_max_hours(course, max_hours)
            ]
        
        if min_score is not None:
            confidence = min(confidence, constraints_confidence)
            filtered_courses = [
                course for course in filtered_courses
                if self._course_above_min_score(course, min_score)
            ]
        
        # Lower confidence if too few or too many results
        if len(filtered_courses) == 0:
            confidence *= 0.5  # Significant confidence reduction for no results
        elif len(filtered_courses) > 50:
            confidence *= 0.9  # Slight confidence reduction for too many results
        
        return filtered_courses, confidence
    
    def _find_semantic_matches(self, query_info: Dict, student_profile: Dict) -> Tuple[List[Dict], float]:
        """Find courses using semantic search based on query and preferences with better concentration handling"""
        semantic_matches = []
        confidence = 0.7  # Base confidence for semantic search
        
        # Skip if we don't have vector search capabilities
        if not hasattr(self.db, 'vector_search'):
            return [], 0.0
        
        # Create a semantic query from the original query and preferences
        semantic_query = query_info["original_query"]
        
        # Add concentration-specific terms to the query
        if student_profile.get("concentration"):
            concentration = student_profile["concentration"]
            semantic_query += f" {concentration}"
            
            # Add expanded terms for interdisciplinary concentrations
            if "Social Studies" in concentration:
                semantic_query += " politics government sociology economics history social theory"
            elif "History and Literature" in concentration:
                semantic_query += " literary historical analysis cultural studies"
            # Add more special cases as needed
        
        # Add explicit preferences to the semantic query
        if query_info["preferences"]:
            pref_terms = []
            for pref in query_info["preferences"]:
                # Convert preference terms to natural language
                if pref == "easy":
                    pref_terms.append("easy manageable workload")
                elif pref == "hard":
                    pref_terms.append("challenging rigorous")
                elif pref == "interesting":
                    pref_terms.append("interesting engaging")
                elif pref == "practical":
                    pref_terms.append("practical applied")
                elif pref == "theoretical":
                    pref_terms.append("theoretical conceptual")
                elif pref.startswith("interest:"):
                    interest = pref.split(":", 1)[1]
                    pref_terms.append(f"about {interest}")
                else:
                    pref_terms.append(pref)
            
            if pref_terms:
                semantic_query += f" {' '.join(pref_terms)}"
        
        # Cache key to avoid redundant searches
        cache_key = f"semantic:{semantic_query}"
        if cache_key in self.search_cache:
            return self.search_cache[cache_key], confidence
        
        # Perform vector search
        try:
            semantic_matches = self.db.vector_search(semantic_query, top_k=20)
            
            # Store in cache
            self.search_cache[cache_key] = semantic_matches
            
            # Adjust confidence based on results
            if len(semantic_matches) == 0:
                confidence *= 0.5  # Significant confidence reduction for no results
            elif len(semantic_matches) < 5:
                confidence *= 0.8  # Slight confidence reduction for few results
            
        except Exception as e:
            print(f"Error in semantic search: {str(e)}")
            confidence = 0.0
            semantic_matches = []
        
        return semantic_matches, confidence
    
    def _determine_most_relevant(self, results: Dict, query_info: Dict, student_profile: Dict) -> Tuple[List[Dict], float]:
        """Determine the most relevant courses using a hybrid ranking approach"""
        # Track sources for the final result set
        sources = {
            "specific": results["specific_courses"],
            "filtered": results["filtered_courses"],
            "semantic": results["semantic_matches"],
            "level": results["level_courses"],
            "term": results["term_courses"]
        }
        
        # Initialize with confidence tracking
        confidence = 0.0
        
        # Start with highest precision results - specific courses
        if sources["specific"]:
            relevant = list(sources["specific"])
            confidence = self.confidence_scores["specific_courses"]
        # Next try filtered courses (explicit criteria match)
        elif sources["filtered"]:
            relevant = list(sources["filtered"])
            confidence = self.confidence_scores["filtered_courses"]
        # Next try semantic matches (implicit criteria)
        elif sources["semantic"]:
            relevant = list(sources["semantic"])
            confidence = self.confidence_scores["semantic_matches"]
        # Fall back to level courses
        elif sources["level"]:
            relevant = list(sources["level"])
            confidence = self.confidence_scores["level_courses"]
        # Last resort: term courses
        elif sources["term"]:
            relevant = list(sources["term"])
            confidence = self.confidence_scores["term_courses"]
        else:
            # No relevant courses found
            return [], 0.0
        
        # Reranking with hybrid approach
        if relevant:
            # Prepare for reranking
            course_ranks = {}
            for course in relevant:
                if 'course_id' not in course:
                    continue
                course_id = course['course_id']
                course_ranks[course_id] = {
                    'course': course,
                    'score': 0.0
                }
            
            # Function to calculate preference match score
            def preference_match_score(course: Dict, preferences: List[str]) -> float:
                score = 0.0
                
                # Check each preference
                for pref in preferences:
                    # Easy courses: higher score for lower hours
                    if pref == "easy" and 'mean_hours' in course and course['mean_hours']:
                        try:
                            hours = float(course['mean_hours'])
                            score += max(0, 20 - hours) / 20  # Max bonus for <5 hours
                        except (ValueError, TypeError):
                            pass
                    
                    # Hard courses: higher score for higher hours
                    elif pref == "hard" and 'mean_hours' in course and course['mean_hours']:
                        try:
                            hours = float(course['mean_hours'])
                            score += min(hours, 20) / 20  # Max bonus for >20 hours
                        except (ValueError, TypeError):
                            pass
                    
                    # Interest-based preferences: semantic matching would capture these
                    elif pref.startswith("interest:") and hasattr(self.db, 'model'):
                        # Already handled by semantic search, but could add extra boost here
                        score += 0.2
                    
                return score / max(1, len(preferences))  # Normalize by number of preferences
            
            # Score by Q Guide rating (if available)
            for course_id, rank_data in course_ranks.items():
                course = rank_data['course']
                base_score = 0.0
                
                # Score based on Q Guide rating (50% weight)
                if 'overall_score_course_mean' in course and course['overall_score_course_mean']:
                    try:
                        q_score = float(course['overall_score_course_mean'])
                        base_score += 0.5 * (q_score / 5.0)  # Normalize to 0-0.5 range
                    except (ValueError, TypeError):
                        pass
                
                # Score based on preference match (30% weight)
                if query_info["preferences"]:
                    pref_score = preference_match_score(course, query_info["preferences"])
                    base_score += 0.3 * pref_score
                
                # Bonus for courses in student's concentration (20% weight)
                if student_profile["concentration"] and 'department' in course:
                    if course['department'] == student_profile["concentration"]:
                        base_score += 0.2
                
                # ADDED: Give a baseline score even for courses with null days/times fields
                # This ensures courses without these fields are still included in results
                if course.get('days') is None or course.get('start_times') is None or course.get('end_times') is None:
                    # Give a small boost to ensure it's not filtered out entirely
                    # but don't artificially inflate its ranking
                    base_score += 0.05
                
                # Store the score
                rank_data['score'] = base_score
            
            # Sort by score (descending)
            sorted_courses = [
                rank_data['course'] 
                for course_id, rank_data in sorted(
                    course_ranks.items(), 
                    key=lambda x: x[1]['score'], 
                    reverse=True
                )
            ]
            
            # FIXED: Check if user is asking for ALL courses
            # Look for keywords like "all", "list all", "show all" in the query
            query_lower = query_info.get("original_query", "").lower()
            if "all" in query_lower or "every" in query_lower or "list all" in query_lower:
                # Return all courses, no limit
                return sorted_courses, confidence
            else:
                # For normal queries, return top 10 for better readability
                return sorted_courses[:10], confidence
        
        return [], 0.0
    
    def _verify_results(self, results: Dict, query_info: Dict, student_profile: Dict) -> List[str]:
        """Verify results against requirements and identify potential issues"""
        verification = []
        
        # Check if we found any courses
        if not results["relevant_courses"] and not results["specific_courses"]:
            verification.append("No courses found matching the criteria")
            
            # Try to identify the reason
            if query_info["course_levels"] and query_info["departments"]:
                verification.append(f"No courses found for levels {query_info['course_levels']} in departments {query_info['departments']}")
            
            if query_info["constraints"].get("max_hours") is not None:
                verification.append(f"The max hours constraint of {query_info['constraints']['max_hours']} may be too restrictive")
            
            if query_info["constraints"].get("min_score") is not None:
                verification.append(f"The min score constraint of {query_info['constraints']['min_score']} may be too restrictive")
        
        # Check if courses match term requirements
        if query_info["terms"] and results["relevant_courses"]:
            term_matches = [
                course for course in results["relevant_courses"]
                if any(
                    term.lower() in course.get('term', '').lower() 
                    for term in query_info["terms"]
                )
            ]
            
            if not term_matches:
                verification.append(f"Warning: None of the relevant courses match the requested term(s): {', '.join(query_info['terms'])}")
        
        # Check if courses match level requirements
        if query_info["course_levels"] and results["relevant_courses"]:
            level_matches = []
            
            for course in results["relevant_courses"]:
                if 'class_tag' in course and isinstance(course['class_tag'], str):
                    match = re.search(r'([A-Za-z]+)\s*(\d+)', course['class_tag'])
                    if match:
                        num = int(match.group(2))
                        for start_level, end_level in query_info["course_levels"]:
                            if start_level <= num <= end_level:
                                level_matches.append(course)
                                break
            
            if not level_matches:
                level_ranges = []
                for start, end in query_info["course_levels"]:
                    if start == end:
                        level_ranges.append(f"{start}")
                    else:
                        level_ranges.append(f"{start}-{end}")
                verification.append(f"Warning: None of the relevant courses match the requested level(s): {', '.join(level_ranges)}")
        
        # Check prerequisites for recommended courses
        for course in results["relevant_courses"]:
            if 'course_requirements' in course and course['course_requirements']:
                # Check if the course has prerequisites that student hasn't taken
                prereq_str = str(course['course_requirements'])
                if 'prerequisite' in prereq_str.lower() or 'prereq' in prereq_str.lower():
                    verification.append(f"Note: {course.get('class_tag', 'Course')} has prerequisites: {prereq_str}")
        
        # Check courses against student profile
        if student_profile["concentration"] and results["relevant_courses"]:
            concentration_matches = [
                course for course in results["relevant_courses"]
                if (
                    'department' in course and 
                    course['department'] == student_profile["concentration"]
                )
            ]
            
            if not concentration_matches and len(results["relevant_courses"]) > 0:
                verification.append(f"Note: None of the relevant courses are in the student's concentration ({student_profile['concentration']})")
        
        # Check for courses student has already taken
        if student_profile["courses_taken"] and results["relevant_courses"]:
            for course in results["relevant_courses"]:
                if 'class_tag' in course:
                    class_tag = course['class_tag']
                    if any(taken.upper() == class_tag.upper() for taken in student_profile["courses_taken"]):
                        verification.append(f"Warning: {class_tag} is in the results but has already been taken by the student")
        
        return verification
    
    def find_similar_courses(self, course_code: str, top_k: int = 5) -> List[Dict]:
        """Find courses similar to the given course using hybrid approach"""
        # Check if we have this query in cache
        cache_key = f"similar:{course_code}:{top_k}"
        if cache_key in self.search_cache:
            return self.search_cache[cache_key]
        
        # Use database's similar course finder if available
        if hasattr(self.db, 'find_similar_courses'):
            similar_courses = self.db.find_similar_courses(course_code, top_k=top_k)
            
            # Cache results
            self.search_cache[cache_key] = similar_courses
            
            return similar_courses
        
        # Fallback to traditional approach
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
                return 0 if not x.get('overall_score_course_mean') or pd.isna(x.get('overall_score_course_mean')) else -float(x.get('overall_score_course_mean'))
            except (ValueError, TypeError):
                return 0
        
        similar_courses.sort(key=sort_key)
        
        # Cache results
        similar_courses_limited = similar_courses[:top_k]
        self.search_cache[cache_key] = similar_courses_limited
        
        return similar_courses_limited
    
    def _course_matches_dept(self, course: Dict, dept: str) -> bool:
        """Check if course matches department"""
        try:
            # Check if dept is in class_tag
            if 'class_tag' in course and isinstance(course['class_tag'], str):
                class_tag = course.get('class_tag', '').upper()
                dept_upper = dept.upper()
                
                # Direct match in class_tag
                if dept_upper in class_tag:
                    return True
                    
                # Special handling for Social Studies
                if dept_upper in ["SOCIAL STUDIES", "SOC-STD", "SOCSTD", "SOC STD"] and \
                any(tag in class_tag for tag in ["SOC-STD", "SOCSTD", "SOC STD"]):
                    return True
                    
                # Check for dept at beginning of class_tag (common format)
                match = re.search(r'^([A-Za-z-]+)\s*\d+', class_tag)
                if match and match.group(1) == dept_upper:
                    return True
                    
                # Check through dept_map if available
                if hasattr(self.db, 'dept_map') and self.db.dept_map:
                    # Loop through all mappings to find matches
                    for alias, full_name in self.db.dept_map.items():
                        # If dept matches alias and class_tag contains that alias
                        if dept_upper == alias.upper() and alias.upper() in class_tag:
                            return True
                        # If dept matches full name and class_tag contains the alias
                        if dept_upper == full_name.upper() and alias.upper() in class_tag:
                            return True
            
            # Check department field (if available)
            if 'department' in course and isinstance(course['department'], str):
                course_dept = course.get('department', '').upper()
                dept_upper = dept.upper()
                
                # Direct match
                if course_dept == dept_upper:
                    return True
                    
                # Special handling for Social Studies
                if dept_upper in ["SOCIAL STUDIES", "SOC-STD", "SOCSTD", "SOC STD"] and \
                any(sd in course_dept for sd in ["SOCIAL STUDIES", "SOC STD", "SOCSTD", "SOC-STD"]):
                    return True
                    
            # Check subject field (if available)
            if 'subject' in course and isinstance(course['subject'], str):
                course_subject = course.get('subject', '').upper()
                dept_upper = dept.upper()
                
                # Direct match
                if course_subject == dept_upper:
                    return True
                    
                # Special handling for Social Studies
                if dept_upper in ["SOCIAL STUDIES", "SOC-STD", "SOCSTD", "SOC STD"] and \
                any(sd in course_subject for sd in ["SOCIAL STUDIES", "SOC STD", "SOCSTD", "SOC-STD"]):
                    return True
                    
            return False
        except Exception:
            # Robust error handling
            return False
    
    def _course_matches_term(self, course: Dict, term: str) -> bool:
        """Check if course matches term with extra flexibility"""
        # Direct string-based term matching
        if 'term' in course and isinstance(course['term'], str):
            # Case-insensitive contains match
            if term.lower() in course['term'].lower():
                return True
                
            # Try exact matching term only (e.g., "Fall" would match "2025 Fall")
            term_parts = term.lower().split()
            course_term_parts = course['term'].lower().split()
            
            # Check if all term parts are in course term
            if all(part in course_term_parts for part in term_parts):
                return True
        
        return False
    
    def _course_above_min_score(self, course: Dict, min_score: float) -> bool:
        """Check if course is above minimum score"""
        if 'overall_score_course_mean' in course and course['overall_score_course_mean'] is not None:
            try:
                return float(course['overall_score_course_mean']) >= min_score
            except (ValueError, TypeError):
                return False
        return False  # If no score, don't include
    
    def _course_below_max_hours(self, course: Dict, max_hours: float) -> bool:
        """Check if course is below maximum hours"""
        if 'mean_hours' in course and course['mean_hours'] is not None:
            try:
                return float(course['mean_hours']) <= max_hours
            except (ValueError, TypeError):
                return True  # If can't convert, include by default
        return True  # If no hours data, include by default