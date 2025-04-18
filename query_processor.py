"""
query_processor.py - Query Analysis Module

This module analyzes user queries to extract key information and understand intentions.
It provides structured data about the query for the course finder and recommender.
"""

import re
from typing import Dict, List, Optional, Tuple, Set, Any

class QueryProcessor:
    """Process and analyze user queries"""
    
    def __init__(self, query: str, chat_history: List[Dict], last_query_info: Optional[Dict] = None):
        """Initialize with the query and chat history"""
        self.query = query
        self.chat_history = chat_history
        self.last_query_info = last_query_info
    
    def process(self) -> Dict:
        """Process the query and extract key information"""
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
            "intent": "unknown"
        }
        
        # Check if this is a follow-up question
        query_info["is_followup"] = self._is_followup_question(query_lower)
        
        # Extract departments
        query_info["departments"] = self._extract_departments(query_lower)
        
        # Extract course levels
        query_info["course_levels"] = self._extract_course_levels(query_lower)
        
        # Extract specific course codes
        query_info["course_codes"] = self._extract_course_codes(query_lower)
        
        # Extract terms
        query_info["terms"] = self._extract_terms(query_lower)
        
        # Extract constraints
        query_info["constraints"] = self._extract_constraints(query_lower)
        
        # Extract referenced courses from follow-up questions
        if query_info["is_followup"]:
            query_info["referenced_courses"] = self._extract_referenced_courses(query_lower)
        
        # Extract preferences
        query_info["preferences"] = self._extract_preferences(query_lower)
        
        # Determine intent
        query_info["intent"] = self._determine_intent(query_lower, query_info)
        
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
            
            if not query_info["course_levels"] and self.last_query_info.get("course_levels"):
                query_info["course_levels"] = self.last_query_info["course_levels"]
            
            if not query_info["course_codes"] and self.last_query_info.get("course_codes"):
                query_info["course_codes"] = self.last_query_info["course_codes"]
        
        return query_info
    
    def _is_followup_question(self, query_lower: str) -> bool:
        """Determine if the query is a follow-up question"""
        # Check for follow-up indicators
        followup_indicators = [
            r'\bit\b',  # "it"
            r'\bthat\b',  # "that"
            r'\bthose\b',  # "those"
            r'\bthis\b',  # "this"
            r'\bthe course\b',  # "the course"
            r'\bcompare\b',  # "compare"
            r'\bbetween\b',  # "between"
            r'\binstead\b',  # "instead"
            r'^what about',  # "what about..."
            r'^how about',  # "how about..."
        ]
        
        for indicator in followup_indicators:
            if re.search(indicator, query_lower):
                return True
        
        # If the query is very short, it's likely a follow-up
        if len(query_lower.split()) <= 5:
            return True
        
        return False
    
    def _extract_departments(self, query_lower: str) -> List[str]:
        """Extract department names from the query"""
        departments = []
        
        # Common department patterns
        dept_patterns = {
            r'\b(math|mathematics)\b': 'MATH',
            r'\b(compsci|cs|computer science)\b': 'COMPSCI',
            r'\b(econ|economics)\b': 'ECON',
            r'\b(gov|government)\b': 'GOV',
            r'\b(physics)\b': 'PHYSICS',
            r'\b(chem|chemistry)\b': 'CHEM',
            r'\b(hist|history)\b': 'HIST',
            r'\b(eng|english)\b': 'ENG',
            r'\b(phil|philosophy)\b': 'PHIL',
            r'\b(stats|statistics)\b': 'STAT',
        }
        
        for pattern, dept in dept_patterns.items():
            if re.search(pattern, query_lower):
                departments.append(dept)
        
        # Also look for capitalized abbreviations that might be departments
        abbrev_match = re.findall(r'\b([A-Z]{2,})\b', self.query)
        for abbrev in abbrev_match:
            if abbrev not in departments:
                departments.append(abbrev)
        
        return departments
    
    def _extract_course_levels(self, query_lower: str) -> List[Tuple[int, int]]:
        """Extract course level ranges from the query"""
        level_ranges = []
        
        # Pattern for decade level (e.g., "100-level", "130s")
        decade_pattern = r'(\d+)(?:\d*)(s|-level| level)?'
        for match in re.finditer(decade_pattern, query_lower):
            base = int(match.group(1))
            suffix = match.group(2)
            
            if suffix and 's' in suffix:
                # e.g., "130s" means 130-139
                level_ranges.append((base, base + 9))
            elif suffix and 'level' in suffix:
                # e.g., "100-level" means 100-199
                level_ranges.append((base, base + 99))
            else:
                # Just a number, might be a specific course
                level_ranges.append((base, base))
        
        return level_ranges
    
    def _extract_course_codes(self, query_lower: str) -> List[str]:
        """Extract specific course codes from the query"""
        # Pattern for course codes like "MATH 136" or "CS 50"
        course_codes = []
        
        # Look for department + number patterns
        for dept in self._extract_departments(query_lower):
            # Look for the department followed by a number
            pattern = rf'{dept.lower()}\s*(\d+)'
            for match in re.finditer(pattern, query_lower):
                num = match.group(1)
                course_codes.append(f"{dept} {num}")
        
        # Also look for explicit course codes (capitalized)
        code_pattern = r'([A-Z]{2,})\s*(\d+)'
        for match in re.finditer(code_pattern, self.query):  # Use original case
            dept = match.group(1)
            num = match.group(2)
            course_codes.append(f"{dept} {num}")
        
        return list(set(course_codes))  # Remove duplicates
    
    def _extract_terms(self, query_lower: str) -> List[str]:
        """Extract terms (semesters) from the query"""
        terms = []
        
        # Pattern for terms
        term_patterns = {
            r'\b(fall)\b': 'Fall',
            r'\b(spring)\b': 'Spring',
            r'\b(summer)\b': 'Summer',
            r'\b(winter)\b': 'Winter',
        }
        
        for pattern, term in term_patterns.items():
            if re.search(pattern, query_lower):
                terms.append(term)
        
        # Look for years
        year_pattern = r'\b(20\d{2})\b'
        years = re.findall(year_pattern, query_lower)
        
        # Combine terms with years if both present
        if terms and years:
            combined_terms = []
            for term in terms:
                for year in years:
                    combined_terms.append(f"{term} {year}")
            return combined_terms
        
        return terms
    
    def _extract_constraints(self, query_lower: str) -> Dict:
        """Extract constraints like max hours or minimum score"""
        constraints = {
            "max_hours": None,
            "min_score": None
        }
        
        # Look for max hours constraints
        hour_patterns = [
            r'(?:less than|no more than|maximum|max) (\d+) hours',
            r'under (\d+) hours',
            r'(\d+) hours or less',
        ]
        
        for pattern in hour_patterns:
            match = re.search(pattern, query_lower)
            if match:
                constraints["max_hours"] = float(match.group(1))
                break
        
        # Look for minimum score constraints
        score_patterns = [
            r'(?:at least|minimum) (\d+(?:\.\d+)?) (?:rating|score)',
            r'(?:rating|score) (?:of )?(?: at least)? (\d+(?:\.\d+)?)',
        ]
        
        for pattern in score_patterns:
            match = re.search(pattern, query_lower)
            if match:
                constraints["min_score"] = float(match.group(1))
                break
        
        # Look for qualitative workload constraints
        if re.search(r'(?:easy|easiest|light workload|manageable|not too (?:much|hard|difficult)|don\'t want to spend too much time)', query_lower):
            if constraints["max_hours"] is None:
                constraints["max_hours"] = 10.0  # Default "easy" threshold
        
        return constraints
    
    def _extract_referenced_courses(self, query_lower: str) -> List[str]:
        """Extract courses referenced in follow-up questions"""
        referenced_courses = []
        
        # Look for explicit course references
        course_pattern = r'([A-Za-z]+)\s*(\d+)'
        for match in re.finditer(course_pattern, query_lower):
            dept = match.group(1).upper()
            num = match.group(2)
            referenced_courses.append(f"{dept} {num}")
        
        # If no explicit references, look for the last mentioned course in chat history
        if not referenced_courses and len(self.chat_history) >= 2:
            last_response = self.chat_history[-1].get("content", "").lower()
            
            # Look for course codes in the last response
            for match in re.finditer(course_pattern, last_response):
                dept = match.group(1).upper()
                num = match.group(2)
                referenced_courses.append(f"{dept} {num}")
        
        return referenced_courses
    
    def _extract_preferences(self, query_lower: str) -> List[str]:
        """Extract preferences from the query"""
        preferences = []
        
        # Look for ease/difficulty preferences
        if re.search(r'\b(easy|easiest|simple|straightforward)\b', query_lower):
            preferences.append("easy")
        elif re.search(r'\b(hard|hardest|difficult|challenging)\b', query_lower):
            preferences.append("hard")
        
        # Look for interest area preferences
        interest_areas = {
            r'\b(interesting|engaging|fun)\b': "interesting",
            r'\b(practical|applied|useful|real-world)\b': "practical",
            r'\b(theoretical|theory|conceptual)\b': "theoretical"
        }
        
        for pattern, preference in interest_areas.items():
            if re.search(pattern, query_lower):
                preferences.append(preference)
        
        return preferences
    
    def _determine_intent(self, query_lower: str, query_info: Dict) -> str:
        """Determine the intent of the query"""
        # Check for course recommendation intent
        recommendation_indicators = [
            r'recommend', r'suggest', r'best', r'good', r'appropriate',
            r'what should', r'which (course|class)', r'advise', r'easy',
            r'take', r'options', r'alternatives'
        ]
        
        for indicator in recommendation_indicators:
            if re.search(indicator, query_lower):
                return "course_recommendation"
        
        # Check for specific course information intent
        if query_info["course_codes"] or (query_info["is_followup"] and query_info["referenced_courses"]):
            return "course_information"
        
        # Check for requirements intent
        requirement_indicators = [
            r'requirement', r'required', r'need to take', r'have to take',
            r'fulfill', r'satisfy', r'complete', r'concentration'
        ]
        
        for indicator in requirement_indicators:
            if re.search(indicator, query_lower):
                return "requirements"
        
        # Default to general information
        return "general_information"