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
// REPLACE this function
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
        
        // Make sure historyRes.data is an array
        const chatHistory = Array.isArray(historyRes.data) ? historyRes.data : [];
        setMessages(chatHistory);
        
        const profile = profileRes.data;
        // Add a null check for profile.courses_taken
        const hasInfo = profile && profile.concentration && 
                       profile.year && 
                       Array.isArray(profile.courses_taken) && 
                       profile.courses_taken.length > 0;
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
      
      // REPLACE this part in handleSubmit where you handle course requests
      if (isCourseReq) {
        const code = extractCourseCode(userMessage);
        console.log("Extracted course code:", code);
        
        if (code) {
          try {
            console.log("Fetching course data for:", code);
            const courseRes = await axios.get(`/api/courses/${code}`);
            
            // Create a manual sanitized copy
            const sanitizedData = {};
            
            // Explicitly sanitize each property
            for (const key in courseRes.data) {
              const value = courseRes.data[key];
              if (typeof value === "number" && isNaN(value)) {
                sanitizedData[key] = null;
              } else if (typeof value === "object" && value !== null) {
                sanitizedData[key] = sanitizeForJSON(value);
              } else {
                sanitizedData[key] = value;
              }
            }
            
            courseData = sanitizedData;
            console.log("Sanitized course data:", courseData);
          } catch (err) {
            console.error('Failed to fetch course data:', err);
          }
        }
      }
  
      // Get the AI response
      const response = await axios.post('/api/chat/message', { message: userMessage });
      
      // Check if we have a valid response
      if (!response || !response.data) {
        throw new Error("Received empty response from server");
      }
      
      console.log("API Response:", response.data);
      
      // Extract the text response - this is critical if the history is truncated
      const aiResponseText = response.data.response;
      
      // Try to use the history from the API, but have a fallback
      if (response.data.history && Array.isArray(response.data.history)) {
        try {
          // Attempt to safely use the history
          // Create a deep copy to avoid reference issues
          const safeHistory = JSON.parse(JSON.stringify(response.data.history));
          setMessages(safeHistory);
        } catch (historyErr) {
          console.warn("Could not process history from API, using fallback:", historyErr);
          
          // Fallback: use just the current exchange
          if (aiResponseText) {
            const updatedMessages = [
              ...messages.filter(m => !(m.role === 'assistant' && m.content === 'Sorry, I ran into an error. Try again!')),
              { role: 'user', content: userMessage },
              { role: 'assistant', content: aiResponseText }
            ];
            
            // If this was a course request and we have course data, add it
            if (isCourseReq && courseData) {
              updatedMessages[updatedMessages.length - 1].courseData = courseData;
            }
            
            setMessages(updatedMessages);
          }
        }
      } else if (aiResponseText) {
        // No valid history but we have a response text
        const updatedMessages = [
          ...messages.filter(m => !(m.role === 'assistant' && m.content === 'Sorry, I ran into an error. Try again!')),
          { role: 'user', content: userMessage },
          { role: 'assistant', content: aiResponseText }
        ];
        
        // If this was a course request and we have course data, add it
        if (isCourseReq && courseData) {
          updatedMessages[updatedMessages.length - 1].courseData = courseData;
        }
        
        setMessages(updatedMessages);
      } else {
        // No history and no response text
        throw new Error("Invalid response format from server");
      }
    } catch (err) {
      console.error("Error in handleSubmit:", err);
      
      // Add a friendly error message
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

  // REPLACE the entire normalizeCourseData function
  const normalizeCourseData = (data) => {
    console.log("Original course data:", data);
    
    if (!data) {
      console.error("No course data provided");
      return {};
    }
    
    // Convert the data to a usable object
    let courseData = data;
    
    // If it's a string, we need to parse it safely
    if (typeof data === 'string') {
      try {
        // Replace NaN in the string with null before parsing
        const cleanedString = data
          .replace(/:\s*NaN/g, ': null')
          .replace(/:\s*"NaN"/g, ': null')
          .replace(/NaN/g, 'null');
        
        console.log("Cleaned JSON string for parsing");
        courseData = JSON.parse(cleanedString);
      } catch (e) {
        console.error("Failed to parse course data string:", e);
        
        // If parsing fails completely, return empty object
        return {};
      }
    }
    
    // Sanitize the object to ensure no NaN values
    courseData = sanitizeForJSON(courseData);
    
    // Safe accessor functions
    const safeString = (field) => {
      const val = courseData[field];
      if (val === null || val === undefined || val !== val) return '';
      return String(val).trim();
    };
    
    const safeNumber = (field) => {
      const val = courseData[field];
      if (val === null || val === undefined || val !== val) return null;
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
    
    // Extract core fields with fallbacks
    const code = safeString('class_tag') || '';
    const title = safeString('class_name') || '';
    const description = safeString('description') || '';
    const instructors = parseJsonArray('instructors');
    const instructorStr = Array.isArray(instructors) ? instructors.join(', ') : '';
    const days = parseJsonArray('days');
    const daysStr = Array.isArray(days) ? days.join(', ') : '';
    
    // Build the normalized course object with fallbacks
    const normalized = {
      code: code,
      title: title,
      description: description,
      instructor: instructorStr || '', 
      term: safeString('term') || '',
      rating: safeNumber('overall_score_course_mean'),
      workload: safeNumber('mean_hours'),
      prerequisites: [],
      enrollment: safeNumber('current_enrollment_number'),
      tags: [],
      schedule: daysStr || '',
      qReportLink: safeString('q_report') || '',
      units: safeString('units') || ''
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

  // REPLACE the first part of renderMessageContent function
  const renderMessageContent = (message) => {
    if (message && message.role === 'assistant' && message.courseData) {
      console.log("Found message with courseData:", 
        typeof message.courseData === 'string' 
          ? message.courseData.substring(0, 50) + '...' 
          : message.courseData
      );
      
      try {
        // Normalize the course data with extra safety
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
              {message.content || ''}
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
      } catch (e) {
        console.error("Error rendering course card:", e);
        return (
          <ReactMarkdown remarkPlugins={[remarkGfm]} className="prose dark:prose-dark">
            {message?.content || ''}
          </ReactMarkdown>
        );
      }
    }
    
    return (
      <ReactMarkdown remarkPlugins={[remarkGfm]} className="prose dark:prose-dark">
        {message?.content || ''}
      </ReactMarkdown>
    );
  };

  // Show loading spinner while data is being fetched
  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="animate-spin h-8 w-8 border-4 border-accent-primary border-t-transparent rounded-full"></div>
      </div>
    );
  }

  return (
    <div className="font-sans">
      <Navbar />
      <main className="flex flex-col items-center px-2 sm:px-6 pt-4 pb-36 max-w-4xl mx-auto min-h-screen">
        {Array.isArray(messages) && messages.length === 0 && !sending ? (
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
            {Array.isArray(messages) && messages.map((m, i) => (
              <div
                key={i}
                className={`px-5 py-4 rounded-xl transition-all duration-300 ${
                  m?.role === 'user'
                    ? 'bg-white dark:bg-dark-200 text-gray-800 dark:text-dark-700 border border-gray-200/80 dark:border-dark-400/30 shadow-sm'
                    : 'bg-transparent text-gray-700 dark:text-dark-700'
                }`}
              >
                <div className="text-xs text-gray-400 dark:text-dark-500 mb-2 font-light">
                  {m?.role === 'assistant' ? 'ChatHarvard' : 'You'} • {new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
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
        courses={Array.isArray(coursesToCompare) ? coursesToCompare : []}
      />
    </div>
  );
}

export default Chat;