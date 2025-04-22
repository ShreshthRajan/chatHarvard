import React, { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import Navbar from '../components/Navbar';
import { PaperAirplaneIcon, ArrowPathIcon } from '@heroicons/react/24/outline';
import { CourseComparisonModal } from '../components/CourseComparisonModal';
import CourseCard from '../components/CourseCard';

/**
 * Safely converts an object with NaN values to a JSON-serializable object
 * @param {Object} obj - The object to sanitize
 * @returns {Object} - A new object with all NaN values replaced with null
 */
const sanitizeForJSON = (obj) => {
  // Handle null, undefined, or primitive values
  if (obj === null || obj === undefined) return null;
  if (typeof obj !== 'object') {
    // Handle NaN special case for numbers
    return Number.isNaN(obj) ? null : obj;
  }
  
  // Handle arrays
  if (Array.isArray(obj)) {
    return obj.map(item => sanitizeForJSON(item));
  }
  
  // Handle objects
  const result = {};
  for (const key in obj) {
    if (Object.prototype.hasOwnProperty.call(obj, key)) {
      const value = obj[key];
      if (value !== value) { // This is how you check for NaN in JavaScript
        result[key] = null;
      } else if (typeof value === 'object') {
        result[key] = sanitizeForJSON(value);
      } else {
        result[key] = value;
      }
    }
  }
  return result;
};

function Chat() {
  const navigate = useNavigate();
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(true);
  const [sending, setSending] = useState(false);
  const [hasProfile, setHasProfile] = useState(false);
  const [compareModalOpen, setCompareModalOpen] = useState(false);
  const [coursesToCompare, setCoursesToCompare] = useState([]);
  const messagesEndRef = useRef(null);
  const inputRef = useRef(null);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const token = localStorage.getItem('token');
        if (!token) return navigate('/login');
        axios.defaults.headers.common['Authorization'] = `Bearer ${token}`;
        const [historyRes, profileRes] = await Promise.all([
          axios.get('/api/chat/history'),
          axios.get('/api/profile')
        ]);
        setMessages(historyRes.data);
        const profile = profileRes.data;
        const hasInfo = profile.concentration && profile.year && profile.courses_taken?.length > 0;
        setHasProfile(hasInfo);
        if (!hasInfo) navigate('/profile');
      } catch (err) {
        console.error(err);
        navigate('/login');
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, [navigate]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const isCourseInfoRequest = (text) => {
    const coursePattern = /([A-Za-z]{2,4})\s*(\d{1,3}[A-Za-z]*)/i;
    const lowerText = text.toLowerCase();
    
    // Return true if the text contains a course code and either:
    // 1. Contains one of the specific request phrases OR
    // 2. Contains "course" and one of these related terms: "card", "info", "details", "information"
    return coursePattern.test(text) &&
      !lowerText.includes('compare') &&
      (
        /(what is|tell me about|info on|details about|course information|show me|display)/i.test(text) ||
        (
          lowerText.includes('course') && 
          /(card|info|details|information|description|overview)/i.test(lowerText)
        )
      );
  };

  const extractCourseCode = (text) => {
    const match = text.match(/([A-Za-z]{2,4})\s*(\d{1,3}[A-Za-z]*)/i);
    return match ? `${match[1].toUpperCase()} ${match[2]}` : null;
  };

    // Helper function to replace NaN values with null for JSON serialization
  // Helper function to replace NaN values with null for JSON serialization
const sanitizeForJSON = (obj) => {
  if (obj === null || obj === undefined) return null;
  
  // Handle NaN specifically
  if (typeof obj === 'number' && isNaN(obj)) return null;
  
  if (typeof obj !== 'object') return obj;
  
  // If it's an array, process each element
  if (Array.isArray(obj)) {
    return obj.map(item => sanitizeForJSON(item));
  }
  
  // Process object properties
  const result = {};
  for (const key in obj) {
    if (Object.prototype.hasOwnProperty.call(obj, key)) {
      const value = obj[key];
      
      // Check specifically for NaN
      if (typeof value === 'number' && isNaN(value)) {
        result[key] = null;
      } else if (typeof value === 'object') {
        result[key] = sanitizeForJSON(value);
      } else {
        result[key] = value;
      }
    }
  }
  return result;
};

  // This is the updated part of your handleSubmit function that handles course data
  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!input.trim() || sending) return;
    const userMessage = input.trim();
    setInput('');
    setMessages(prev => [...prev, { role: 'user', content: userMessage }]);
    setSending(true);

    try {
      // Check if this is a course info request
      let courseData = null;
      const isCourseReq = isCourseInfoRequest(userMessage);
      console.log("Is this a course request?", isCourseReq);
      
      if (isCourseReq) {
        const code = extractCourseCode(userMessage);
        console.log("Extracted course code:", code);
        
        if (code) {
          try {
            console.log("Fetching course data for:", code);
            const courseRes = await axios.get(`/api/courses/${code}`);
            
            // IMPORTANT: Sanitize the course data to replace NaN with null
            courseData = sanitizeForJSON(courseRes.data);
            console.log("Sanitized course data:", courseData);
          } catch (err) {
            console.error('Failed to fetch course data:', err);
          }
        }
      }

      // Get the AI response
      const response = await axios.post('/api/chat/message', { message: userMessage });
      let updated = response.data.history;

      // Handle comparison request
      if (userMessage.toLowerCase().includes('compare')) {
        // Your existing comparison logic...
      } 
      // If we have course data, add it to the assistant's message
      else if (courseData) {
        const lastAssistantMsgIndex = [...updated].reverse().findIndex(msg => msg.role === 'assistant');
        if (lastAssistantMsgIndex !== -1) {
          const trueIndex = updated.length - 1 - lastAssistantMsgIndex;
          console.log("Adding course data to assistant message at index:", trueIndex);
          
          // Ensure the course data is properly sanitized
          updated[trueIndex] = {
            ...updated[trueIndex],
            courseData: courseData, // Already sanitized
          };
        }
      }

      setMessages(updated);
    } catch (err) {
      console.error(err);
      setMessages(prev => [...prev, { 
        role: 'assistant', 
        content: 'Sorry, I ran into an error. Try again!' 
      }]);
    } finally {
      setSending(false);
      inputRef.current?.focus();
    }
  };

  const handleClearChat = async () => {
    try {
      await axios.post('/api/chat/clear');
      setMessages([]);
    } catch (err) {
      console.error(err);
    }
  };

  const normalizeCourseData = (data) => {
    console.log("Original course data type:", typeof data);
    
    if (!data) {
      console.error("No course data provided");
      return {};
    }
    
    // Convert the data to a usable object
    let courseData = data;
    
    // If it's a string, we need to parse it, but we need to handle NaN values
    if (typeof data === 'string') {
      try {
        // Replace NaN in the string with null before parsing
        const cleanedString = data
          .replace(/:\s*NaN/g, ': null')
          .replace(/:\s*"NaN"/g, ': null');
        
        console.log("Cleaned JSON string:", cleanedString);
        courseData = JSON.parse(cleanedString);
      } catch (e) {
        console.error("Failed to parse course data string:", e);
        // Try a different approach
        try {
          // Try to evaluate the object directly (careful with this approach)
          // This is needed because JSON.parse doesn't accept NaN
          courseData = eval(`(${data})`);
          // Immediately sanitize to replace any NaN values
          courseData = sanitizeForJSON(courseData);
        } catch (e2) {
          console.error("Failed second parsing attempt:", e2);
          return {}; // Give up and return empty object
        }
      }
    }
    
    console.log("Processed course data:", courseData);
    
    // Extract basic fields with safety checks
    const safeString = (field) => {
      const val = courseData[field];
      if (val === null || val === undefined || Number.isNaN(val)) return '';
      return String(val).trim();
    };
    
    const safeNumber = (field) => {
      const val = courseData[field];
      if (val === null || val === undefined || Number.isNaN(val)) return null;
      const num = parseFloat(val);
      return isNaN(num) ? null : num;
    };
    
    const parseJsonArray = (field) => {
      try {
        const val = courseData[field];
        if (!val) return [];
        
        // Already an array
        if (Array.isArray(val)) return val;
        
        // String that needs parsing
        if (typeof val === 'string') {
          return JSON.parse(val);
        }
        
        return [];
      } catch (e) {
        console.warn(`Failed to parse ${field} as array:`, e);
        return [];
      }
    };
    
    // Extract core fields
    const code = safeString('class_tag');
    const title = safeString('class_name');
    const description = safeString('description');
    const instructors = parseJsonArray('instructors');
    const instructorStr = Array.isArray(instructors) ? instructors.join(', ') : '';
    const days = parseJsonArray('days');
    const daysStr = Array.isArray(days) ? days.join(', ') : '';
    
    // Build the normalized course object
    const normalized = {
      code: code,
      title: title,
      description: description,
      instructor: instructorStr, 
      term: safeString('term'),
      rating: safeNumber('overall_score_course_mean'),
      workload: safeNumber('mean_hours'),
      prerequisites: [],
      enrollment: safeNumber('current_enrollment_number'),
      tags: [],
      schedule: daysStr,
      qReportLink: safeString('q_report'),
      units: safeString('units')
    };
    
    // Add prerequisites
    if (courseData.recommended_prep) {
      normalized.prerequisites.push(courseData.recommended_prep);
    }
    
    if (courseData.course_requirements) {
      normalized.prerequisites.push(courseData.course_requirements);
    }
    
    // Add basic tags
    if (courseData.department) {
      normalized.tags.push(courseData.department);
    }
    
    console.log("Normalized course data:", normalized);
    
    // Log warning if essential fields are missing
    if (!normalized.code || !normalized.title) {
      console.warn('⚠️ Missing key course fields:', normalized);
    }
    
    return normalized;
  };  

  const renderMessageContent = (message) => {
    if (message.role === 'assistant' && message.courseData) {
      console.log("Found message with courseData:", 
        typeof message.courseData === 'string' 
          ? message.courseData.substring(0, 50) + '...' 
          : message.courseData
      );
      
      // Normalize the course data
      const normalized = normalizeCourseData(message.courseData);
      
      // Only render the CourseCard if we have the minimum essential data
      const hasEssentialData = normalized && normalized.code && normalized.title;
      console.log("Has essential data:", hasEssentialData);
      
      if (!hasEssentialData) {
        console.warn("Missing essential course data for rendering card");
      }
      
      return (
        <>
          <ReactMarkdown remarkPlugins={[remarkGfm]} className="prose dark:prose-dark mb-3">
            {message.content}
          </ReactMarkdown>
          
          {hasEssentialData ? (
            <div className="border border-accent-primary/20 dark:border-accent-primary/30 p-4 my-4 rounded-lg shadow-sm bg-white dark:bg-dark-200">
              <CourseCard 
                course={normalized} 
                className="course-card-in-chat"
              />
              {normalized.qReportLink && (
                <div className="text-xs text-gray-500 mt-2 text-right">
                  <a 
                    href={normalized.qReportLink} 
                    target="_blank" 
                    rel="noopener noreferrer" 
                    className="text-accent-primary dark:text-accent-secondary hover:underline"
                  >
                    View Q Report
                  </a>
                </div>
              )}
            </div>
          ) : (
            <div className="text-sm text-gray-400 italic mt-2 bg-gray-50 dark:bg-dark-300/50 p-3 rounded">
              Course card data not available. Try asking for information on a specific course.
            </div>
          )}
        </>
      );
    }
    
    return (
      <ReactMarkdown remarkPlugins={[remarkGfm]} className="prose dark:prose-dark">
        {message.content}
      </ReactMarkdown>
    );
  };

  if (!hasProfile) return null;

  return (
    <div className="font-sans">
      <Navbar />
      <main className="flex flex-col items-center px-2 sm:px-6 pt-4 pb-36 max-w-4xl mx-auto min-h-screen">
        {messages.length === 0 && !sending ? (
          <div className="welcome-message text-center mt-20 animate-fade-in">
            <div className="w-16 h-16 bg-accent-primary/10 dark:bg-accent-primary/20 rounded-full flex items-center justify-center mx-auto mb-6">
              <div className="text-3xl">🎓</div>
            </div>
            <h1 className="text-2xl font-light mb-3 text-gray-900 dark:text-dark-800">
              Welcome to <span className="font-medium text-accent-primary dark:text-accent-secondary">ChatHarvard</span>
            </h1>
            <p className="text-gray-600 dark:text-dark-600 mb-8 max-w-md mx-auto">
              Ask anything about Harvard courses, requirements, or get recommendations.
            </p>
            <div className="grid gap-3">
              {[
                "What courses should I take for Computer Science?",
                "How do I fulfill the Quantitative Reasoning requirement?",
                "Compare CS50 and CS51 workload",
                "What are the prerequisites for ECON 1010?"
              ].map((s, i) => (
                <button
                  key={i}
                  onClick={() => {
                    setInput(s);
                    inputRef.current?.focus();
                  }}
                  className="text-left px-4 py-3 border border-gray-200 dark:border-dark-400/50 rounded-xl bg-white dark:bg-dark-200 hover:border-accent-primary/40 dark:hover:border-accent-primary/40 hover:bg-accent-primary/5 dark:hover:bg-dark-300 transition-all duration-200"
                >
                  {s}
                </button>
              ))}
            </div>
          </div>
        ) : (
          <div className="w-full space-y-5">
            {messages.map((m, i) => (
              <div
                key={i}
                className={`px-5 py-4 rounded-xl transition-all duration-300 ${
                  m.role === 'user'
                    ? 'bg-white dark:bg-dark-200 text-gray-800 dark:text-dark-700 border border-gray-200/80 dark:border-dark-400/30 shadow-sm'
                    : 'bg-transparent text-gray-700 dark:text-dark-700'
                }`}
              >
                <div className="text-xs text-gray-400 dark:text-dark-500 mb-2 font-light">
                  {m.role === 'assistant' ? 'ChatHarvard' : 'You'} • {new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                </div>
                {renderMessageContent(m)}
              </div>
            ))}
            {sending && (
              <div className="flex items-center space-x-2 text-sm text-gray-500 dark:text-dark-600">
                <div className="flex space-x-1">
                  <span className="h-1.5 w-1.5 bg-accent-primary/60 dark:bg-accent-primary/60 rounded-full animate-pulse"></span>
                  <span className="h-1.5 w-1.5 bg-accent-primary/60 dark:bg-accent-primary/60 rounded-full animate-pulse delay-200"></span>
                  <span className="h-1.5 w-1.5 bg-accent-primary/60 dark:bg-accent-primary/60 rounded-full animate-pulse delay-400"></span>
                </div>
                <span className="text-xs font-light">ChatHarvard is thinking...</span>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>
        )}
      </main>

      {/* Sticky Input Bubble */}
      <div className="fixed bottom-0 left-0 right-0 z-50 flex justify-center bg-gradient-to-t from-gray-50 dark:from-dark-100 to-transparent pointer-events-none pb-4 pt-16">
        <div className="w-full max-w-4xl px-4 py-3 pointer-events-auto">
          <button
            onClick={handleClearChat}
            className="text-xs mb-2 px-3 py-1.5 border border-accent-primary/30 bg-accent-primary/10 text-accent-primary hover:text-accent-tertiary rounded-md hover:bg-accent-primary/20 transition"
          >
            <ArrowPathIcon className="h-4 w-4 inline-block mr-1" />
            New Chat
          </button>
          <form onSubmit={handleSubmit} className="relative">
            <textarea
              ref={inputRef}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Ask about Harvard courses..."
              disabled={sending}
              className="w-full border border-gray-200 dark:border-dark-400/50 rounded-xl p-4 pr-12 bg-white dark:bg-dark-200 text-gray-800 dark:text-dark-700 placeholder:text-gray-400 dark:placeholder:text-dark-500 focus:outline-none focus:ring-2 focus:ring-accent-primary/30 dark:focus:ring-accent-primary/30 focus:border-accent-primary/50 dark:focus:border-accent-primary/50 resize-none min-h-[2.5rem] max-h-[160px] shadow-sm"
              rows={1}
              onInput={(e) => {
                e.target.style.height = 'auto';
                e.target.style.height = `${Math.min(e.target.scrollHeight, 160)}px`;
              }}
              onKeyDown={(e) => {
                if (e.key === 'Enter' && !e.shiftKey) {
                  e.preventDefault();
                  handleSubmit(e);
                }
              }}
            />
            <button
              type="submit"
              disabled={sending || !input.trim()}
              className="absolute right-3 bottom-3 p-2 text-accent-primary hover:bg-accent-primary/10 rounded-lg disabled:opacity-50 transition-all duration-200"
            >
              <PaperAirplaneIcon className="h-5 w-5" />
            </button>
          </form>
          <div className="text-xs text-gray-400 dark:text-dark-500 mt-2 text-center">
            Press Enter to send • Shift+Enter for new line
          </div>
        </div>
      </div>

      <CourseComparisonModal
        isOpen={compareModalOpen}
        onClose={() => setCompareModalOpen(false)}
        courses={coursesToCompare}
      />
    </div>
  );
}

export default Chat;