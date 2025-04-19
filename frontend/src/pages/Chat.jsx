import React, { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { PaperAirplaneIcon, ArrowPathIcon } from '@heroicons/react/24/outline';
import Navbar from '../components/Navbar';

function Chat() {
  const navigate = useNavigate();
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(true);
  const [sending, setSending] = useState(false);
  const [hasProfile, setHasProfile] = useState(false);
  const messagesEndRef = useRef(null);
  
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
      setMessages(response.data.history);
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
  
  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex justify-center items-center">
        <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-harvard-crimson"></div>
      </div>
    );
  }
  
  if (!hasProfile) {
    return null; // Will redirect to profile page
  }
  
  return (
    <>
      <Navbar />
      <div className="flex flex-col h-screen bg-gradient-to-b from-gray-50 to-white">
        {/* Enhanced Header */}
        <div className="py-3 border-b border-gray-200 bg-white shadow-sm flex items-center justify-between px-4 md:px-6">
          <div className="flex items-center">
            <span className="text-2xl mr-2">🎓</span>
            <h1 className="text-lg font-semibold bg-clip-text text-transparent bg-gradient-to-r from-harvard-crimson to-harvard-dark">ChatHarvard</h1>
          </div>
          <button
            onClick={handleClearChat}
            className="flex items-center text-sm text-gray-500 hover:text-gray-700 px-3 py-1 rounded-full border border-gray-200 hover:bg-gray-50 transition-colors duration-150"
          >
            <ArrowPathIcon className="h-4 w-4 mr-1" />
            Clear Chat
          </button>
        </div>
        
        {/* Enhanced Messages Container */}
        <div className="flex-1 overflow-y-auto p-4 md:p-6 space-y-4 bg-gray-50">
        {messages.length === 0 && !sending && (
            <div className="flex flex-col items-center justify-center h-full text-center text-gray-500 space-y-4">
              <div className="text-5xl mb-2">🎓</div>
              <h2 className="text-xl font-semibold text-gray-700">Welcome to ChatHarvard</h2>
              <p className="max-w-md text-sm">Your personal academic advisor for Harvard University. Ask me anything about courses, requirements, or get personalized recommendations.</p>
            </div>
          )}
          
          {messages.map((message, index) => (
            <div
              key={index}
              className={`flex ${messages[index].role === 'user' ? 'justify-end' : 'justify-start'} animate-fade-in`}
            >
              <div 
                className={`max-w-3xl p-4 rounded-2xl shadow-sm ${
                  message.role === 'user' 
                    ? 'bg-harvard-light border border-chat-border text-gray-900' 
                    : 'bg-white border border-gray-100 text-gray-800'
                } transition-all duration-300`}
                style={{ width: 'fit-content', maxWidth: '90%' }}
              >
                {message.role === 'assistant' ? (
                  <div className="prose prose-sm max-w-none">
                    <ReactMarkdown remarkPlugins={[remarkGfm]}>
                      {message.content}
                    </ReactMarkdown>
                  </div>
                ) : (
                  <p className="whitespace-pre-wrap">{message.content}</p>
                )}
                <div className="text-xs text-gray-400 mt-2 flex justify-end">
                  {new Date().toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})}
                </div>
              </div>
            </div>
          ))}
          
          {/* Enhanced loading indicator */}
          {sending && (
            <div className="flex justify-start">
              <div className="bg-white border border-gray-100 p-5 rounded-2xl shadow-sm">
                <div className="flex items-center space-x-3">
                  <div className="h-2.5 w-2.5 rounded-full bg-harvard-crimson animate-pulse"></div>
                  <div className="h-2.5 w-2.5 rounded-full bg-harvard-crimson animate-pulse" style={{ animationDelay: '0.2s' }}></div>
                  <div className="h-2.5 w-2.5 rounded-full bg-harvard-crimson animate-pulse" style={{ animationDelay: '0.4s' }}></div>
                </div>
              </div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>
        
        {/* Enhanced Input Container */}
        <div className="border-t border-gray-200 bg-white p-4 md:p-6">
          <form onSubmit={handleSubmit} className="max-w-4xl mx-auto">
            <div className="relative">
              <input
                type="text"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                disabled={sending}
                placeholder="Ask about Harvard courses, requirements, or get recommendations..."
                className="w-full border border-gray-300 rounded-full px-6 py-3.5 pr-16 shadow-sm focus:outline-none focus:ring-2 focus:ring-harvard-crimson focus:border-transparent transition-all duration-200"
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
                className={`absolute right-2 top-1/2 transform -translate-y-1/2 p-2 rounded-full ${
                  sending || !input.trim()
                    ? 'bg-gray-300 text-gray-500 cursor-not-allowed'
                    : 'bg-harvard-crimson text-white hover:bg-harvard-dark'
                } transition-colors shadow-sm`}
              >
                <PaperAirplaneIcon className="h-5 w-5" />
              </button>
            </div>
            <div className="text-xs text-gray-400 text-center mt-2">
              Press Enter to send • Shift+Enter for new line
            </div>
          </form>
        </div>
      </div>
    </>
  );
}

export default Chat;