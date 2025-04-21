import React, { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { PaperAirplaneIcon, ArrowPathIcon } from '@heroicons/react/24/outline';
import Navbar from '../components/Navbar';
import { CourseComparisonModal } from '../components/CourseComparisonModal';
import CourseCard from '../components/CourseCard';

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
  
  // Fetch chat history and profile
  useEffect(() => {
    const fetchData = async () => {
      try {
        const token = localStorage.getItem('token');
        if (!token) {
          navigate('/login');
          return;
        }
  
        axios.defaults.headers.common['Authorization'] = `Bearer ${token}`;
  
        // Get chat history
        const historyResponse = await axios.get('/api/chat/history');
        setMessages(historyResponse.data);
  
        // Check if profile exists
        const profileResponse = await axios.get('/api/profile');
        const profile = profileResponse.data;
  
        const hasRequiredInfo =
          profile.concentration &&
          profile.year &&
          profile.courses_taken &&
          profile.courses_taken.length > 0;
  
        setHasProfile(hasRequiredInfo);
  
        if (!hasRequiredInfo) {
          navigate('/profile');
        }
      } catch (error) {
        console.error('Error fetching data:', error);
        navigate('/login'); // fallback to login on any error
      } finally {
        setLoading(false);
      }
    };
  
    fetchData();
  }, [navigate]);  
  
  // Scroll to bottom when messages change
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);
  
  // Add welcome message if no messages
  useEffect(() => {
    if (!loading && messages.length === 0 && hasProfile) {
      setMessages([
        {
          role: 'assistant',
          content: `👋 Hi there! I'm your Harvard academic advisor.
          
I can help you with:
- Course recommendations based on your interests and profile
- Information about specific courses and their workload
- Concentration requirements
- Comparing different courses
- And much more!

Ask me anything about Harvard academics or try one of these examples:
- "I need a 130s level math class for my concentration. What are my options?"
- "What's the easiest way to fulfill my science requirement?"
- "Compare the workload between CS50 and CS51"`
        }
      ]);
    }
  }, [loading, messages.length, hasProfile]);
  
  // Function to check if the message is a course information request
  const isCourseInfoRequest = (content) => {
    // Check if content contains a course code pattern
    const courseCodePattern = /([A-Za-z]{2,4})\s*(\d{1,3}[A-Za-z]*)/i;
    return courseCodePattern.test(content) && 
           !content.toLowerCase().includes('compare') &&
           (content.toLowerCase().includes('what is') || 
            content.toLowerCase().includes('tell me about') || 
            content.toLowerCase().includes('course information') ||
            content.toLowerCase().includes('info on') ||
            content.toLowerCase().includes('details about'));
  };
  
  // Function to extract course code from message
  const extractCourseCode = (content) => {
    const match = content.match(/([A-Za-z]{2,4})\s*(\d{1,3}[A-Za-z]*)/i);
    if (match) {
      return `${match[1].toUpperCase()} ${match[2]}`;
    }
    return null;
  };
  
  // Generate mock course data
  const generateCourseData = (courseCode) => {
    const mockCourseData = {
      code: courseCode,
      title: `${courseCode} - Sample Course Title`,
      description: "This is a sample course description that would typically provide an overview of the course content, objectives, and learning outcomes. This description helps students understand what to expect from the course.",
      instructor: "Professor Sample",
      term: "Spring 2025",
      rating: 4.2,
      workload: 8,
      prerequisites: ["MATH 1A", "CS 50"],
      enrollment: 120,
      tags: ["Quantitative Reasoning", "Departmental Requirement"]
    };
    
    return mockCourseData;
  };
  
  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!input.trim() || sending) return;
    
    const userMessage = input.trim();
    setInput('');
    
    // Add user message immediately
    setMessages(prev => [...prev, { role: 'user', content: userMessage }]);
    setSending(true);
    
    try {
      const response = await axios.post('/api/chat/message', { message: userMessage });
      
      let updatedResponse = response.data.history;
      
      // Check if response contains course comparison request
      if (userMessage.toLowerCase().includes('compare')) {
        const courseCodes = userMessage.match(/([A-Za-z]{2,4})\s*(\d{1,3}[A-Za-z]*)/g);
        if (courseCodes && courseCodes.length >= 2) {
          // Mock course data - in a real app, you'd fetch from your backend
          setCoursesToCompare([
            {
              courseCode: courseCodes[0],
              title: `Sample Course ${courseCodes[0]}`,
              instructor: "Professor Smith",
              qScore: 4.2,
              workload: 8,
              description: "This is a sample course description for comparison purposes."
            },
            {
              courseCode: courseCodes[1],
              title: `Sample Course ${courseCodes[1]}`,
              instructor: "Professor Johnson",
              qScore: 3.8,
              workload: 12,
              description: "This is another sample course description for comparison purposes."
            }
          ]);
          
          // Wait for state update then open modal
          setTimeout(() => {
            setCompareModalOpen(true);
          }, 500);
        }
      } 
      // Check if this is a specific course information request
      else if (isCourseInfoRequest(userMessage)) {
        const courseCode = extractCourseCode(userMessage);
        if (courseCode) {
          // For course info requests, add a special type to render as a card
          const lastMessage = updatedResponse[updatedResponse.length - 1];
          const courseData = generateCourseData(courseCode);
          
          // Add a courseData property to the message
          updatedResponse[updatedResponse.length - 1] = {
            ...lastMessage,
            courseData
          };
        }
      }
      
      setMessages(updatedResponse);
    } catch (error) {
      console.error('Error sending message:', error);
      // Add error message
      setMessages(prev => [
        ...prev, 
        { 
          role: 'assistant', 
          content: 'Sorry, I encountered an error processing your request. Please try again.' 
        }
      ]);
    } finally {
      setSending(false);
      // Focus the input field after sending
      inputRef.current?.focus();
    }
  };
  
  const handleClearChat = async () => {
    try {
      await axios.post('/api/chat/clear');
      setMessages([]);
    } catch (error) {
      console.error('Error clearing chat:', error);
    }
  };
  
  // Function to render course card when appropriate
  const renderMessageContent = (message) => {
    if (message.role === 'assistant' && message.courseData) {
      return (
        <div className="mb-4">
          <div className="prose prose-sm max-w-none dark:prose-dark mb-4">
            <ReactMarkdown remarkPlugins={[remarkGfm]}>
              {message.content}
            </ReactMarkdown>
          </div>
          <div className="mt-4 bg-white dark:bg-dark-300 rounded-lg shadow-sm overflow-hidden border border-gray-200 dark:border-dark-400">
            <CourseCard course={message.courseData} />
          </div>
        </div>
      );
    } else if (message.role === 'assistant') {
      return (
        <div className="prose prose-sm max-w-none dark:prose-dark">
          <ReactMarkdown remarkPlugins={[remarkGfm]}>
            {message.content}
          </ReactMarkdown>
        </div>
      );
    } else {
      return (
        <p className="whitespace-pre-wrap">{message.content}</p>
      );
    }
  };
  
  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 dark:bg-dark-100 flex justify-center items-center transition-colors">
        <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-accent-primary"></div>
      </div>
    );
  }
  
  if (!hasProfile) {
    return null; // Will redirect to profile page
  }
  
  return (
    <>
      <Navbar />
      <div className="flex flex-col h-screen bg-gray-50 dark:bg-dark-100 transition-colors">
        {/* Chat container */}
        <div className="flex-1 overflow-hidden flex flex-col">
          {/* Messages container with Claude.ai-like styling */}
          <div className="flex-1 overflow-y-auto px-4 md:px-6 max-w-4xl mx-auto w-full">
            {messages.length === 0 && !sending && (
              <div className="flex flex-col items-center justify-center h-full welcome-message">
                <div className="text-4xl mb-2">🎓</div>
                <h2>Welcome to ChatHarvard</h2>
                <p>Your personal academic advisor for Harvard University. Ask me anything about courses, requirements, or get personalized recommendations.</p>
              </div>
            )}
            
            <div className="message-container space-y-1 py-6">
              {messages.map((message, index) => (
                <div
                  key={index}
                  className="animate-fade-in mb-6"
                >
                  <div className="flex items-center space-x-2 text-xs text-gray-500 dark:text-dark-500 mb-1">
                    <span className="font-medium">
                      {message.role === 'assistant' ? 'ChatHarvard' : 'You'}
                    </span>
                    <span className="text-gray-400 dark:text-dark-600">•</span>
                    <span className="text-gray-400 dark:text-dark-600">{new Date().toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})}</span>
                  </div>
                  <div 
                    className={`py-2 ${
                      message.role === 'user' 
                        ? 'pl-3 border-l-2 border-gray-300 dark:border-dark-500' 
                        : ''
                    }`}
                  >
                    {renderMessageContent(message)}
                  </div>
                </div>
              ))}
              
              {/* Enhanced loading indicator */}
              {sending && (
                <div className="animate-fade-in mb-6">
                  <div className="flex items-center space-x-2 text-xs text-gray-500 dark:text-dark-500 mb-1">
                    <span className="font-medium">ChatHarvard</span>
                    <span className="text-gray-400 dark:text-dark-600">•</span>
                    <span className="text-gray-400 dark:text-dark-600">{new Date().toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})}</span>
                  </div>
                  <div className="py-2">
                    <div className="flex items-center space-x-3">
                      <div className="h-2 w-2 rounded-full bg-accent-primary animate-pulse"></div>
                      <div className="h-2 w-2 rounded-full bg-accent-primary animate-pulse" style={{ animationDelay: '0.2s' }}></div>
                      <div className="h-2 w-2 rounded-full bg-accent-primary animate-pulse" style={{ animationDelay: '0.4s' }}></div>
                    </div>
                  </div>
                </div>
              )}
            </div>
            <div ref={messagesEndRef} />
          </div>
          
          {/* Input container - fixed at bottom with Claude.ai-like styling */}
          <div className="border-t border-gray-200 dark:border-dark-400 bg-white dark:bg-dark-200 py-4 px-4 md:px-6 transition-colors">
            <div className="max-w-4xl mx-auto">
              <div className="flex items-center justify-between mb-3">
                <button
                  onClick={handleClearChat}
                  className="flex items-center text-xs text-gray-500 dark:text-dark-600 hover:text-gray-700 dark:hover:text-dark-700 px-3 py-1 rounded-md border border-gray-200 dark:border-dark-400 hover:bg-gray-50 dark:hover:bg-dark-300 transition-colors duration-150"
                >
                  <ArrowPathIcon className="h-3 w-3 mr-1" />
                  Clear Chat
                </button>
              </div>
              
              <form onSubmit={handleSubmit} className="relative">
                <input
                  type="text"
                  ref={inputRef}
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  disabled={sending}
                  placeholder="Ask about Harvard courses, requirements, or get recommendations..."
                  className="w-full border border-gray-300 dark:border-dark-400 rounded-lg px-6 py-3 pr-16 shadow-sm focus:outline-none focus:ring-2 focus:ring-accent-primary focus:border-transparent dark:bg-dark-300 dark:text-dark-700 dark:placeholder-dark-500 transition-all duration-200"
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
                  className={`absolute right-2 top-1/2 transform -translate-y-1/2 p-2.5 rounded-lg ${
                    sending || !input.trim()
                      ? 'bg-gray-300 dark:bg-dark-400 text-gray-500 dark:text-dark-500 cursor-not-allowed'
                      : 'bg-accent-primary text-white hover:bg-accent-tertiary'
                  } transition-colors shadow-sm`}
                >
                  <PaperAirplaneIcon className="h-5 w-5" />
                </button>
                <div className="text-xs text-gray-400 dark:text-dark-500 text-center mt-2">
                  Press Enter to send • Shift+Enter for new line
                </div>
              </form>
            </div>
          </div>
        </div>
      </div>
      
      {/* Course Comparison Modal */}
      <CourseComparisonModal 
        isOpen={compareModalOpen} 
        onClose={() => setCompareModalOpen(false)} 
        courses={coursesToCompare} 
      />
    </>
  );
}

export default Chat;