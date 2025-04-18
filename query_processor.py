"""
query_processor.py - Enhanced Query Analysis Module

This module analyzes user queries to extract key information and understand intentions
using advanced NLP techniques. It provides structured data about the query for the
course finder and recommender with self-reflection capabilities.
"""

import re
import nltk
from typing import Dict, List, Optional, Tuple, Set, Any
from collections import defaultdict
import numpy as np

class QueryProcessor:
    """Process and analyze user queries with advanced intent recognition and self-reflection"""
    
    def __init__(self, query: str, chat_history: List[Dict], last_query_info: Optional[Dict] = None):
        """Initialize with the query and chat history"""
        self.query = query
        self.chat_history = chat_history
        self.last_query_info = last_query_info
        
        # Initialize cache for processed parts
        self.cache = {}
        
        # Initialize confidence scores for different extracted elements
        self.confidence = {
            "intent": 0.0,
            "departments": 0.0,
            "course_levels": 0.0,
            "course_codes": 0.0,
            "terms": 0.0,
            "constraints": 0.0,
            "preferences": 0.0,
            "is_followup": 0.0
        }
        
        # Initialize self-reflection results
        self.self_reflection = {
            "missing_information": [],
            "ambiguities": [],
            "verification_needed": []
        }
    
    def process(self) -> Dict:
        """Process the query and extract key information with self-reflection"""
        # Convert query to lowercase for case-insensitive matching
        query_lower = self.query.lower()
        
        # Initialize extracted information
        query_info = {
            "original_query": self.query,
            "departments": [],
            "course_levels": [],
            "course_codes": [],
            "terms": [],
            "constraints": {
                "max_hours": None,
                "min_score": None
            },
            "is_followup": False,
            "referenced_courses": [],
            "preferences": [],
            "intent": "unknown",
            "confidence_scores": {},
            "self_reflection": {
                "missing_information": [],
                "ambiguities": [],
                "verification_needed": []
            },
            "semantic_aspects": {
                "difficulty": None,  # easy, moderate, hard
                "interest_level": None,  # high, medium, low
                "relevance": None,  # career, personal, degree
                "format": None  # lecture, seminar, project-based
            },
            "implicit_preferences": []
        }
        
        # Check if this is a follow-up question
        query_info["is_followup"], self.confidence["is_followup"] = self._is_followup_question(query_lower)
        
        # Extract intent
        query_info["intent"], self.confidence["intent"] = self._extract_intent(query_lower)
        
        # Extract departments
        query_info["departments"], self.confidence["departments"] = self._extract_departments(query_lower)
        
        # Extract course levels
        query_info["course_levels"], self.confidence["course_levels"] = self._extract_course_levels(query_lower)
        
        # Extract specific course codes
        query_info["course_codes"], self.confidence["course_codes"] = self._extract_course_codes(query_lower)
        
        # Extract terms
        query_info["terms"], self.confidence["terms"] = self._extract_terms(query_lower)
        
        # Extract constraints
        query_info["constraints"], self.confidence["constraints"] = self._extract_constraints(query_lower)
        
        # Extract referenced courses from follow-up questions
        if query_info["is_followup"]:
            query_info["referenced_courses"], ref_confidence = self._extract_referenced_courses(query_lower)
        
        # Extract preferences
        query_info["preferences"], self.confidence["preferences"] = self._extract_preferences(query_lower)
        
        # Extract semantic aspects
        query_info["semantic_aspects"] = self._extract_semantic_aspects(query_lower)
        
        # Extract implicit preferences
        query_info["implicit_preferences"] = self._extract_implicit_preferences(query_lower)
        
        # If this is a follow-up with no specific course details, inherit from previous query
        if query_info["is_followup"] and not any([
            query_info["departments"], 
            query_info["course_levels"], 
            query_info["course_codes"],
            query_info["referenced_courses"]
        ]) and self.last_query_info:
            # Inherit relevant information from previous query
            if not query_info["departments"] and self.last_query_info.get("departments"):
                query_info["departments"] = self.last_query_info["departments"]
                self.confidence["departments"] = 0.7  # Reduced confidence for inherited info
            
            if not query_info["course_levels"] and self.last_query_info.get("course_levels"):
                query_info["course_levels"] = self.last_query_info["course_levels"]
                self.confidence["course_levels"] = 0.7
            
            if not query_info["course_codes"] and self.last_query_info.get("course_codes"):
                query_info["course_codes"] = self.last_query_info["course_codes"]
                self.confidence["course_codes"] = 0.7
                
            if not query_info["terms"] and self.last_query_info.get("terms"):
                query_info["terms"] = self.last_query_info["terms"]
                self.confidence["terms"] = 0.7
                
            if not query_info["constraints"].get("max_hours") and self.last_query_info.get("constraints", {}).get("max_hours"):
                query_info["constraints"]["max_hours"] = self.last_query_info["constraints"]["max_hours"]
                self.confidence["constraints"] = 0.7
                
            if not query_info["constraints"].get("min_score") and self.last_query_info.get("constraints", {}).get("min_score"):
                query_info["constraints"]["min_score"] = self.last_query_info["constraints"]["min_score"]
                self.confidence["constraints"] = 0.7
        
        # Self-reflection to identify missing information
        self._perform_self_reflection(query_info)
        query_info["self_reflection"] = self.self_reflection
        
        # Store confidence scores
        query_info["confidence_scores"] = dict(self.confidence)
        
        return query_info
    
    def _is_followup_question(self, query_lower: str) -> Tuple[bool, float]:
        """Determine if the query is a follow-up question and confidence level"""
        confidence = 0.0
        is_followup = False
        
        # Check for follow-up indicators
        followup_indicators = [
            (r'\bit\b', 0.6),  # "it"
            (r'\bthat\b', 0.7),  # "that"
            (r'\bthose\b', 0.75),  # "those"
            (r'\bthis\b', 0.65),  # "this"
            (r'\bthe course\b', 0.8),  # "the course"
            (r'\bcompare\b', 0.7),  # "compare"
            (r'\bbetween\b', 0.6),  # "between"
            (r'\binstead\b', 0.75),  # "instead"
            (r'^what about', 0.9),  # "what about..."
            (r'^how about', 0.9),  # "how about..."
            (r'\balso\b', 0.6),  # "also"
            (r'\btoo\b', 0.6),  # "too"
            (r'\banother\b', 0.7),  # "another"
            (r'\bsimilar\b', 0.65),  # "similar"
            (r'\balternatives?\b', 0.8),  # "alternative(s)"
        ]
        
        for pattern, conf in followup_indicators:
            if re.search(pattern, query_lower):
                is_followup = True
                confidence = max(confidence, conf)
        
        # If the query is very short, it's likely a follow-up
        if len(query_lower.split()) <= 5:
            is_followup = True
            shortness_confidence = 0.5 + 0.1 * (5 - len(query_lower.split()))  # More confidence for shorter queries
            confidence = max(confidence, shortness_confidence)
        
        # Check if this explicitly references a previous response
        if len(self.chat_history) >= 2 and self.chat_history[-1]["role"] == "assistant":
            last_assistant_msg = self.chat_history[-1]["content"].lower()
            
            # Check if any course mentioned in the last message appears in this query
            course_pattern = r'([A-Za-z]+)\s*(\d+)'
            last_msg_courses = re.findall(course_pattern, last_assistant_msg)
            for dept, num in last_msg_courses:
                if re.search(f'{dept}\\s*{num}', query_lower, re.IGNORECASE):
                    is_followup = True
                    confidence = max(confidence, 0.85)
        
        return is_followup, confidence
    
    def _extract_intent(self, query_lower: str) -> Tuple[str, float]:
        """Extract query intent with confidence score"""
        # Define patterns and confidence scores for each intent
        intent_patterns = {
            "course_recommendation": [
                (r'recommend', 0.9),
                (r'suggest', 0.9),
                (r'best', 0.8),
                (r'good', 0.7),
                (r'appropriate', 0.7),
                (r'what should', 0.8),
                (r'which (course|class)', 0.85),
                (r'advise', 0.9),
                (r'easy', 0.6),
                (r'take', 0.75),
                (r'options', 0.7),
                (r'alternatives', 0.7),
                (r'chillest', 0.85),  # Specific slang for easy courses
                (r'manageable', 0.75),
                (r'interesting', 0.6),
                (r'fun', 0.6)
            ],
            "course_information": [
                (r'what is', 0.7),
                (r'tell me about', 0.85),
                (r'details', 0.8),
                (r'information about', 0.9),
                (r'describe', 0.85),
                (r'explain', 0.8),
                (r'learn about', 0.75),
                (r'syllabus', 0.9),
                (r'professor', 0.7),
                (r'instructor', 0.7),
                (r'taught by', 0.8),
                (r'reading', 0.6),
                (r'topics', 0.7),
                (r'assignments', 0.8),
                (r'prerequisites', 0.8)
            ],
            "requirements": [
                (r'requirement', 0.9),
                (r'required', 0.9),
                (r'need to take', 0.85),
                (r'have to take', 0.85),
                (r'fulfill', 0.8),
                (r'satisfy', 0.8),
                (r'complete', 0.7),
                (r'concentration', 0.75),
                (r'major', 0.75),
                (r'minor', 0.75),
                (r'degree', 0.8),
                (r'program', 0.7),
                (r'grad(uate|uation)', 0.8),
                (r'credits?', 0.75)
            ],
            "comparison": [
                (r'compare', 0.9),
                (r'difference', 0.85),
                (r'better', 0.8),
                (r'easier', 0.8),
                (r'harder', 0.8),
                (r'versus', 0.9),
                (r'vs\.?', 0.9),
                (r'or', 0.6),
                (r'similar', 0.7),
                (r'between', 0.8)
            ],
            "schedule_planning": [
                (r'schedule', 0.85),
                (r'timetable', 0.85),
                (r'conflict', 0.8),
                (r'overlapping', 0.8),
                (r'time', 0.6),
                (r'semester plan', 0.9),
                (r'course load', 0.85),
                (r'workload', 0.8),
                (r'balance', 0.7),
                (r'fit', 0.6)
            ]
        }
        
        # Calculate scores for each intent
        intent_scores = defaultdict(float)
        
        for intent, patterns in intent_patterns.items():
            for pattern, conf in patterns:
                if re.search(pattern, query_lower):
                    intent_scores[intent] = max(intent_scores[intent], conf)
        
        # Check for specific course codes which would indicate course information
        course_pattern = r'([A-Za-z]+)\s*(\d+)'
        if re.search(course_pattern, query_lower):
            # If asking about a specific course without other indicators, likely course information
            if not any(s > 0 for s in intent_scores.values()):
                intent_scores["course_information"] = 0.7
            # If asking about a specific course with recommendation signals, boost recommendation score
            elif intent_scores.get("course_recommendation", 0) > 0:
                intent_scores["course_recommendation"] += 0.2
        
        # Get the highest scoring intent
        if intent_scores:
            max_intent = max(intent_scores.items(), key=lambda x: x[1])
            intent, confidence = max_intent
        else:
            # Default to general information with low confidence
            intent = "general_information"
            confidence = 0.3
        
        return intent, confidence
    
    def _extract_departments(self, query_lower: str) -> Tuple[List[str], float]:
        """Extract department names from the query with confidence score"""
        departments = []
        confidence = 0.0
        
        # Common department patterns with confidence values
        dept_patterns = {
            r'\b(math|mathematics)\b': ('MATH', 0.9),
            r'\b(compsci|cs|computer science)\b': ('COMPSCI', 0.9),
            r'\b(econ|economics)\b': ('ECON', 0.9),
            r'\b(gov|government)\b': ('GOV', 0.9),
            r'\b(physics)\b': ('PHYSICS', 0.9),
            r'\b(chem|chemistry)\b': ('CHEM', 0.9),
            r'\b(hist|history)\b': ('HIST', 0.9),
            r'\b(eng|english)\b': ('ENG', 0.85),
            r'\b(phil|philosophy)\b': ('PHIL', 0.9),
            r'\b(stats|statistics)\b': ('STAT', 0.9),
            r'\b(bio|biology)\b': ('BIO', 0.9),
            r'\b(psych|psychology)\b': ('PSY', 0.9),
            r'\b(sociol|sociology)\b': ('SOC', 0.9),
            r'\b(anthro|anthropology)\b': ('ANTHRO', 0.9),
            r'\b(astro|astronomy)\b': ('ASTRON', 0.9),
            r'\b(applied math|applied mathematics)\b': ('APMTH', 0.9),
            r'\b(music)\b': ('MUSIC', 0.9),
            r'\b(art|art history)\b': ('ART', 0.85),
            r'\b(theater|theatre)\b': ('TDM', 0.8),
            r'\b(language)\b': ('LANG', 0.7),
            r'\b(french)\b': ('FRENCH', 0.9),
            r'\b(spanish)\b': ('SPANISH', 0.9),
            r'\b(german)\b': ('GERMAN', 0.9),
            r'\b(chinese)\b': ('CHINESE', 0.9),
            r'\b(japanese)\b': ('JAPANESE', 0.9),
            r'\b(classics)\b': ('CLASSIC', 0.9),
            r'\b(neuro|neuroscience)\b': ('NEURO', 0.9),
            r'\b(earth|earth science)\b': ('EPS', 0.85),
            r'\b(engineering)\b': ('ENG', 0.7),
            r'\b(education)\b': ('EDU', 0.85),
        }
        
        for pattern, (dept, conf) in dept_patterns.items():
            if re.search(pattern, query_lower):
                departments.append(dept)
                confidence = max(confidence, conf)
        
        # Also look for capitalized abbreviations that might be departments
        abbrev_match = re.findall(r'\b([A-Z]{2,})\b', self.query)
        for abbrev in abbrev_match:
            if abbrev not in departments:
                departments.append(abbrev)
                confidence = max(confidence, 0.8)  # Confidence for explicit abbreviation
        
        # Check if confidence needs adjustment
        if len(departments) > 1:
            # Multiple departments might indicate lower confidence in each
            confidence = max(0.6, confidence - 0.1)
        elif len(departments) == 0:
            confidence = 0.0
        
        return departments, confidence
    
    def _extract_course_levels(self, query_lower: str) -> Tuple[List[Tuple[int, int]], float]:
        """Extract course level ranges from the query with confidence score"""
        level_ranges = []
        confidence = 0.0
        
        # Pattern for decade level (e.g., "100-level", "130s")
        decade_patterns = [
            (r'(\d+)s\b', 0.9),  # 130s
            (r'(\d+)0s\b', 0.9),  # 130s
            (r'(\d+)-level', 0.9),  # 100-level
            (r'level (\d+)', 0.8),  # level 100
            (r'(\d+) level', 0.8),  # 100 level
        ]
        
        for pattern, conf in decade_patterns:
            for match in re.finditer(pattern, query_lower):
                base = int(match.group(1))
                
                # Handle different cases
                if 'level' in match.group(0):
                    # 100-level means 100-199
                    if base % 100 == 0:
                        level_ranges.append((base, base + 99))
                        confidence = max(confidence, conf)
                    else:
                        # 130-level would be 130-139
                        tens_digit = (base // 10) % 10
                        if tens_digit != 0:
                            base_level = (base // 10) * 10
                            level_ranges.append((base_level, base_level + 9))
                            confidence = max(confidence, conf)
                        else:
                            level_ranges.append((base, base + 9))
                            confidence = max(confidence, conf * 0.9)  # Slightly lower confidence
                else:
                    # 130s means 130-139
                    if base % 10 == 0:
                        level_ranges.append((base, base + 9))
                        confidence = max(confidence, conf)
                    else:
                        # Adjust to the decade
                        base_level = (base // 10) * 10
                        level_ranges.append((base_level, base_level + 9))
                        confidence = max(confidence, conf * 0.8)  # Lower confidence for adjustment
        
        # Look for explicit ranges like "130-139" or "130 to 139"
        range_patterns = [
            r'(\d+)[\s-]+to[\s-]+(\d+)',
            r'(\d+)[\s-]+through[\s-]+(\d+)',
            r'(\d+)[\s-]*-[\s-]*(\d+)',
            r'between (\d+) and (\d+)',
        ]
        
        for pattern in range_patterns:
            for match in re.finditer(pattern, query_lower):
                start, end = int(match.group(1)), int(match.group(2))
                level_ranges.append((start, end))
                confidence = max(confidence, 0.95)  # High confidence for explicit ranges
        
        # Check for single course numbers that might not be explicit levels
        number_pattern = r'\b(\d+)\b'
        for match in re.finditer(number_pattern, query_lower):
            num = int(match.group(1))
            
            # Skip if this number is part of an already detected range
            if any(start <= num <= end for start, end in level_ranges):
                continue
            
            # Only consider 2-3 digit numbers not starting with 0
            if 10 <= num <= 999:
                # Is this a single course number or a level?
                context_before = query_lower[:match.start()].strip()
                context_after = query_lower[match.end():].strip()
                
                is_level = False
                level_indicators = ['level', 'levels', 'hundred', 'course level']
                
                for indicator in level_indicators:
                    if indicator in context_before[-15:] or indicator in context_after[:15]:
                        is_level = True
                        break
                
                if is_level:
                    # Treat as a level, e.g., "100" means 100-199
                    if num % 100 == 0:
                        level_ranges.append((num, num + 99))
                        confidence = max(confidence, 0.8)
                    elif num % 10 == 0:
                        # e.g., "130" means 130-139
                        level_ranges.append((num, num + 9))
                        confidence = max(confidence, 0.75)
                    else:
                        # Not a typical level number, might be a specific course
                        level_ranges.append((num, num))
                        confidence = max(confidence, 0.5)  # Lower confidence
                else:
                    # Might be a specific course number, not a level
                    level_ranges.append((num, num))
                    confidence = max(confidence, 0.4)  # Lower confidence for ambiguous cases
        
        return level_ranges, confidence
    
    def _extract_course_codes(self, query_lower: str) -> Tuple[List[str], float]:
        """Extract specific course codes from the query with confidence score"""
        # Pattern for course codes like "MATH 136" or "CS 50"
        course_codes = []
        confidence = 0.0
        
        # General pattern for department + number
        general_pattern = r'([A-Za-z]{2,})\s*(\d+)'
        
        # Extract from the original query to preserve case
        for match in re.finditer(general_pattern, self.query):
            dept = match.group(1).upper()
            num = match.group(2)
            course_codes.append(f"{dept} {num}")
            confidence = max(confidence, 0.9)  # High confidence for explicit course codes
        
        # Look for department + number patterns with known departments
        detected_depts, _ = self._extract_departments(query_lower)
        for dept in detected_depts:
            # Look for the department followed by a number
            pattern = rf'{dept.lower()}\s*(\d+)'
            for match in re.finditer(pattern, query_lower):
                num = match.group(1)
                course_code = f"{dept} {num}"
                if course_code not in course_codes:
                    course_codes.append(course_code)
                    confidence = max(confidence, 0.85)
        
        return list(set(course_codes)), confidence  # Remove duplicates
    
    def _extract_terms(self, query_lower: str) -> Tuple[List[str], float]:
        """Extract terms (semesters) from the query with confidence score"""
        terms = []
        confidence = 0.0
        
        # Pattern for terms with confidence values
        term_patterns = {
            r'\b(fall)\b': ('Fall', 0.9),
            r'\b(spring)\b': ('Spring', 0.9),
            r'\b(summer)\b': ('Summer', 0.9),
            r'\b(winter)\b': ('Winter', 0.9),
            r'\bnext semester\b': ('Spring', 0.8),  # Assuming current semester is Fall
            r'\bthis semester\b': ('Fall', 0.75),   # Assuming current semester is Fall
            r'\bcurrent semester\b': ('Fall', 0.75),
            r'\bnext term\b': ('Spring', 0.7),
            r'\bthis term\b': ('Fall', 0.7),
            r'\bnext year\b': ('Fall', 0.6),  # Less confident
            r'\bupcoming\b': ('Spring', 0.6), # Less confident
        }
        
        for pattern, (term, conf) in term_patterns.items():
            if re.search(pattern, query_lower):
                terms.append(term)
                confidence = max(confidence, conf)
        
        # Look for years
        year_pattern = r'\b(20\d{2})\b'
        years = re.findall(year_pattern, query_lower)
        
        year_confidence = 0.9 if years else 0.0
        
        # Combine terms with years if both present
        if terms and years:
            combined_terms = []
            for term in terms:
                for year in years:
                    combined_terms.append(f"{term} {year}")
            return combined_terms, min(confidence, year_confidence)
        
        # Handle short forms like "F23" or "S24"
        short_form_pattern = r'\b([FS])(\d{2})\b'
        for match in re.finditer(short_form_pattern, query_lower):
            season, yr = match.groups()
            term = "Fall" if season.upper() == "F" else "Spring"
            year = f"20{yr}"
            terms.append(f"{term} {year}")
            confidence = max(confidence, 0.85)
        
        return terms, confidence
    
    def _extract_constraints(self, query_lower: str) -> Tuple[Dict, float]:
        """Extract constraints like max hours or minimum score with confidence"""
        constraints = {
            "max_hours": None,
            "min_score": None
        }
        confidence = 0.0
        
        # Look for max hours constraints
        hour_patterns = [
            (r'(?:less than|no more than|maximum|max) (\d+) hours', 0.9),
            (r'under (\d+) hours', 0.85),
            (r'(\d+) hours or less', 0.85),
            (r'not more than (\d+) hours', 0.85),
            (r'at most (\d+) hours', 0.85),
            (r'fewer than (\d+) hours', 0.85),
            (r'< (\d+) hours', 0.9),
            (r'≤ (\d+) hours', 0.9),
        ]
        
        for pattern, conf in hour_patterns:
            match = re.search(pattern, query_lower)
            if match:
                constraints["max_hours"] = float(match.group(1))
                confidence = max(confidence, conf)
                break
        
        # Look for minimum score constraints
        score_patterns = [
            (r'(?:at least|minimum) (\d+(?:\.\d+)?) (?:rating|score)', 0.9),
            (r'(?:rating|score) (?:of )?(?: at least)? (\d+(?:\.\d+)?)', 0.8),
            (r'(?:rating|score) (?:above|higher than) (\d+(?:\.\d+)?)', 0.85),
            (r'better than (\d+(?:\.\d+)?) (?:rating|score)', 0.8),
            (r'> (\d+(?:\.\d+)?) (?:rating|score)', 0.9),
            (r'≥ (\d+(?:\.\d+)?) (?:rating|score)', 0.9),
        ]
        
        for pattern, conf in score_patterns:
            match = re.search(pattern, query_lower)
            if match:
                constraints["min_score"] = float(match.group(1))
                confidence = max(confidence, conf)
                break
        
        # Look for qualitative workload constraints
        workload_indicators = [
            (r'(?:easy|easiest|light workload|manageable)', 0.8),
            (r'not too (?:much|hard|difficult)', 0.75),
            (r'don\'t want to spend too much time', 0.75),
            (r'low commitment', 0.7),
            (r'less work', 0.7),
            (r'minimal effort', 0.75),
            (r'(?:chill|chillest)', 0.85),  # Slang for easy
        ]
        
        for pattern, conf in workload_indicators:
            if re.search(pattern, query_lower):
                if constraints["max_hours"] is None:
                    constraints["max_hours"] = 10.0  # Default "easy" threshold
                    confidence = max(confidence, conf)
        
        # Look for qualitative score constraints
        score_indicators = [
            (r'(?:good|great|excellent|high) (?:rating|score|reviews)', 0.8),
            (r'well-rated', 0.8),
            (r'highly-rated', 0.85),
            (r'top-rated', 0.85),
            (r'good q score', 0.85),
            (r'people like', 0.7),
            (r'well-reviewed', 0.8),
        ]
        
        for pattern, conf in score_indicators:
            if re.search(pattern, query_lower):
                if constraints["min_score"] is None:
                    constraints["min_score"] = 4.0  # Default "good" threshold
                    confidence = max(confidence, conf)
        
        return constraints, confidence
    
    def _extract_referenced_courses(self, query_lower: str) -> Tuple[List[str], float]:
        """Extract courses referenced in follow-up questions with confidence"""
        referenced_courses = []
        confidence = 0.0
        
        # Look for explicit course references
        course_pattern = r'([A-Za-z]+)\s*(\d+)'
        for match in re.finditer(course_pattern, query_lower):
            dept = match.group(1).upper()
            num = match.group(2)
            referenced_courses.append(f"{dept} {num}")
            confidence = max(confidence, 0.9)  # High confidence for explicit references
        
        # If no explicit references, look for the last mentioned course in chat history
        if not referenced_courses and len(self.chat_history) >= 2:
            last_response = self.chat_history[-1].get("content", "").lower()
            
            # Look for course codes in the last response
            for match in re.finditer(course_pattern, last_response):
                dept = match.group(1).upper()
                num = match.group(2)
                referenced_courses.append(f"{dept} {num}")
                confidence = max(confidence, 0.7)  # Lower confidence for implicit references
        
        # Look for pronouns referring to courses
        if not referenced_courses and re.search(r'\b(it|this|that|this course|that course)\b', query_lower):
            if len(self.chat_history) >= 2:
                last_response = self.chat_history[-1].get("content", "").lower()
                
                # Look for the first course mentioned in the last response
                for match in re.finditer(course_pattern, last_response):
                    dept = match.group(1).upper()
                    num = match.group(2)
                    referenced_courses.append(f"{dept} {num}")
                    confidence = max(confidence, 0.6)  # Even lower confidence for pronoun references
                    break  # Just take the first one
        
        return referenced_courses, confidence
    
    def _extract_preferences(self, query_lower: str) -> Tuple[List[str], float]:
        """Extract preferences from the query with confidence scores"""
        preferences = []
        confidence = 0.0
        
        # Define preference patterns with confidence values
        preference_patterns = {
            # Ease/difficulty preferences
            "easy": [
                (r'\b(easy|easiest|simple|straightforward)\b', 0.9),
                (r'\b(light|manageable|reasonable|chill|chillest)\b', 0.85),
                (r'\b(gentle|introductory|beginner|basic)\b', 0.8),
                (r'not too (hard|difficult|challenging|demanding|heavy)', 0.75),
                (r'low (workload|time commitment|effort)', 0.8)
            ],
            "hard": [
                (r'\b(hard|hardest|difficult|challenging)\b', 0.9),
                (r'\b(rigorous|demanding|advanced|tough|intense)\b', 0.85),
                (r'\b(comprehensive|thorough|deep|complex)\b', 0.8),
                (r'not too (easy|simple|basic)', 0.75),
                (r'high (difficulty|challenge)', 0.8)
            ],
            
            # Interest area preferences
            "interesting": [
                (r'\b(interesting|engaging|fun|enjoyable|exciting)\b', 0.85),
                (r'\b(fascinating|captivating|inspiring|stimulating)\b', 0.8),
                (r'not (boring|dull|dry)', 0.75)
            ],
            "practical": [
                (r'\b(practical|applied|useful|real-world|hands-on)\b', 0.85),
                (r'\b(applicable|relevant|industry|career|skill)\b', 0.8),
                (r'not (theoretical|abstract)', 0.75)
            ],
            "theoretical": [
                (r'\b(theoretical|theory|conceptual|abstract|fundamental)\b', 0.85),
                (r'\b(philosophical|foundational|academic|intellectual)\b', 0.8),
                (r'not (practical|applied)', 0.75)
            ],
            
            # Format preferences
            "lecture": [
                (r'\b(lecture|lectures|traditional)\b', 0.85),
                (r'professor (talks|teaching|explaining)', 0.75)
            ],
            "discussion": [
                (r'\b(discussion|seminar|interactive|participation)\b', 0.85),
                (r'\b(debate|conversation|dialogue|talk)\b', 0.75)
            ],
            "project": [
                (r'\b(project|projects|hands-on|practical|lab|labs)\b', 0.85),
                (r'\b(building|creating|making|coding|programming)\b', 0.8),
                (r'\b(application|applied|implementing)\b', 0.75)
            ],
            
            # Grading preferences
            "fair_grading": [
                (r'\b(fair|consistent|transparent|reasonable) (grading|assessment)\b', 0.85),
                (r'clear expectations', 0.8),
                (r'not (harsh|strict|arbitrary) grading', 0.75)
            ],
            "easy_grading": [
                (r'\b(easy|generous|lenient) (grading|assessment)\b', 0.85),
                (r'grade inflation', 0.8),
                (r'high (grades|scores)', 0.75),
                (r'easy (A|B)', 0.85)
            ]
        }
        
        # Check each preference pattern
        for preference, patterns in preference_patterns.items():
            for pattern, conf in patterns:
                if re.search(pattern, query_lower):
                    preferences.append(preference)
                    confidence = max(confidence, conf)
                    break  # Only add each preference once
        
        # Look for subject interest patterns
        subject_interest_patterns = [
            (r'interested in ([\w\s]+)', 0.8),
            (r'like ([\w\s]+)', 0.7),
            (r'enjoy ([\w\s]+)', 0.75),
            (r'passion for ([\w\s]+)', 0.85),
            (r'curious about ([\w\s]+)', 0.75)
        ]
        
        for pattern, conf in subject_interest_patterns:
            match = re.search(pattern, query_lower)
            if match:
                subject = match.group(1).strip()
                if len(subject.split()) <= 3:  # Limit to short subjects
                    preferences.append(f"interest:{subject}")
                    confidence = max(confidence, conf)
        
        return preferences, confidence
    
    def _extract_semantic_aspects(self, query_lower: str) -> Dict[str, Optional[str]]:
        """Extract semantic aspects of the query like difficulty preference"""
        aspects = {
            "difficulty": None,  # easy, moderate, hard
            "interest_level": None,  # high, medium, low
            "relevance": None,  # career, personal, degree
            "format": None  # lecture, seminar, project-based
        }
        
        # Extract difficulty preference
        difficulty_patterns = {
            "easy": [
                r'\b(easy|easiest|simple|straightforward|light|manageable|chill|chillest)\b',
                r'not too (hard|difficult|challenging|demanding)',
                r'low (workload|time commitment|effort)'
            ],
            "moderate": [
                r'\b(moderate|balanced|medium|intermediate|reasonable)\b',
                r'not too (easy|hard)',
                r'middle ground',
                r'balanced (workload|difficulty)'
            ],
            "hard": [
                r'\b(hard|hardest|difficult|challenging|rigorous|demanding|advanced|tough|intense)\b',
                r'not too (easy|simple)',
                r'high (difficulty|challenge|level)'
            ]
        }
        
        for level, patterns in difficulty_patterns.items():
            if any(re.search(pattern, query_lower) for pattern in patterns):
                aspects["difficulty"] = level
                break
        
        # Extract interest level
        interest_patterns = {
            "high": [
                r'\b(interesting|fascinating|captivating|exciting|engaging|fun)\b',
                r'really (like|enjoy|love)',
                r'passion for',
                r'favorite'
            ],
            "medium": [
                r'\b(somewhat interesting|moderately engaging)\b',
                r'kind of (like|enjoy)',
                r'might (like|enjoy)'
            ],
            "low": [
                r'not (boring|dull|dry)',
                r'don\'t (hate|dislike)',
                r'tolerable',
                r'get through'
            ]
        }
        
        for level, patterns in interest_patterns.items():
            if any(re.search(pattern, query_lower) for pattern in patterns):
                aspects["interest_level"] = level
                break
        
        # Extract relevance
        relevance_patterns = {
            "career": [
                r'\b(career|job|profession|industry|work|employment)\b',
                r'future (job|work|career)',
                r'after graduation',
                r'professional'
            ],
            "personal": [
                r'\b(interest|hobby|personal|passion|curious|enjoy)\b',
                r'for fun',
                r'personally',
                r'just for me'
            ],
            "degree": [
                r'\b(requirement|requirements|required|concentration|major|minor|degree|graduate|graduation)\b',
                r'need for (major|degree|graduation)',
                r'have to take',
                r'fulfill'
            ]
        }
        
        for relevance, patterns in relevance_patterns.items():
            if any(re.search(pattern, query_lower) for pattern in patterns):
                aspects["relevance"] = relevance
                break
        
        # Extract format preference
        format_patterns = {
            "lecture": [
                r'\b(lecture|lectures|traditional|instructor-led)\b',
                r'professor (talks|teaching|explaining)',
                r'listening'
            ],
            "seminar": [
                r'\b(discussion|seminar|interactive|participation|small class)\b',
                r'\b(debate|conversation|dialogue|talk)\b',
                r'discussing'
            ],
            "project-based": [
                r'\b(project|projects|hands-on|practical|lab|labs|workshop)\b',
                r'\b(building|creating|making|coding|programming)\b',
                r'\b(application|applied|implementing)\b',
                r'creating'
            ]
        }
        
        for format_type, patterns in format_patterns.items():
            if any(re.search(pattern, query_lower) for pattern in patterns):
                aspects["format"] = format_type
                break
        
        return aspects
    
    def _extract_implicit_preferences(self, query_lower: str) -> List[str]:
        """Extract implicit preferences that might not be explicitly stated"""
        implicit_prefs = []
        
        # Look for subtle indicators of preferences
        
        # Preference for prestigious courses
        prestige_patterns = [
            r'best',
            r'top',
            r'prestigious',
            r'renowned',
            r'famous',
            r'well-known',
            r'popular'
        ]
        
        if any(re.search(pattern, query_lower) for pattern in prestige_patterns):
            implicit_prefs.append("high_prestige")
        
        # Preference for small classes
        small_class_patterns = [
            r'small',
            r'intimate',
            r'not too big',
            r'fewer students',
            r'individual attention'
        ]
        
        if any(re.search(pattern, query_lower) for pattern in small_class_patterns):
            implicit_prefs.append("small_class")
        
        # Preference for good professors
        good_prof_patterns = [
            r'good professor',
            r'great teacher',
            r'excellent instructor',
            r'engaging faculty',
            r'best taught'
        ]
        
        if any(re.search(pattern, query_lower) for pattern in good_prof_patterns):
            implicit_prefs.append("good_professor")
        
        # Preference for minimal writing
        minimal_writing_patterns = [
            r'not much writing',
            r'minimal papers',
            r'few essays',
            r'no papers',
            r'not essay-based'
        ]
        
        if any(re.search(pattern, query_lower) for pattern in minimal_writing_patterns):
            implicit_prefs.append("minimal_writing")
        
        # Preference for minimal reading
        minimal_reading_patterns = [
            r'not much reading',
            r'light reading',
            r'few readings',
            r'minimal reading',
            r'not reading-heavy'
        ]
        
        if any(re.search(pattern, query_lower) for pattern in minimal_reading_patterns):
            implicit_prefs.append("minimal_reading")
        
        # Preference for courses with good social aspects
        social_patterns = [
            r'friends',
            r'social',
            r'collaborate',
            r'group work',
            r'meet people',
            r'team'
        ]
        
        if any(re.search(pattern, query_lower) for pattern in social_patterns):
            implicit_prefs.append("social")
        
        return implicit_prefs
    
    def _perform_self_reflection(self, query_info: Dict) -> None:
        """Perform self-reflection to identify potential issues with the query analysis"""
        # Check for missing information
        if not query_info["departments"] and not query_info["course_codes"]:
            self.self_reflection["missing_information"].append("No department or course specified")
        
        if not query_info["course_levels"] and not query_info["course_codes"]:
            self.self_reflection["missing_information"].append("No course level specified")
        
        if not query_info["terms"]:
            self.self_reflection["missing_information"].append("No term/semester specified")
        
        # Check for ambiguities
        if len(query_info["departments"]) > 1:
            self.self_reflection["ambiguities"].append(f"Multiple departments specified: {', '.join(query_info['departments'])}")
        
        if len(query_info["course_levels"]) > 1:
            level_strs = []
            for start, end in query_info["course_levels"]:
                if start == end:
                    level_strs.append(f"{start}")
                else:
                    level_strs.append(f"{start}-{end}")
            self.self_reflection["ambiguities"].append(f"Multiple course levels specified: {', '.join(level_strs)}")
        
        # Check for potential conflicts in preferences
        preferences = query_info["preferences"]
        if "easy" in preferences and "hard" in preferences:
            self.self_reflection["ambiguities"].append("Conflicting difficulty preferences")
        
        if "practical" in preferences and "theoretical" in preferences:
            self.self_reflection["ambiguities"].append("Conflicting style preferences")
        
        # Check for verification needs
        if self.confidence["intent"] < 0.7:
            self.self_reflection["verification_needed"].append("Intent is unclear")
        
        if query_info["is_followup"] and not query_info["referenced_courses"] and self.confidence["is_followup"] < 0.8:
            self.self_reflection["verification_needed"].append("Follow-up reference is unclear")
        
        # Check for constraints that might be too restrictive
        if query_info["constraints"].get("max_hours") is not None and query_info["constraints"].get("max_hours") < 5:
            self.self_reflection["verification_needed"].append(f"Very low max hours constraint: {query_info['constraints']['max_hours']}")
        
        if query_info["constraints"].get("min_score") is not None and query_info["constraints"].get("min_score") > 4.5:
            self.self_reflection["verification_needed"].append(f"Very high minimum score constraint: {query_info['constraints']['min_score']}")