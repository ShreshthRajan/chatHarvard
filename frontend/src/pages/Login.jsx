import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import axios from 'axios';
import { toast } from 'react-hot-toast';

function Login() {
  const { currentUser, setCurrentUser, setAuthProvider } = useAuth();
  const navigate = useNavigate();
  
  const [provider, setProvider] = useState('openai');
  const [apiKey, setApiKey] = useState('');
  const [loading, setLoading] = useState(false);
  const [validating, setValidating] = useState(false);
  const [error, setError] = useState('');
  const [shareableLink, setShareableLink] = useState('');
  const [showShareLink, setShowShareLink] = useState(false);

  useEffect(() => {
    if (currentUser) {
      navigate('/');
    }
    
    // Generate a shareable link when component mounts
    const baseUrl = window.location.origin;
    const randomId = Math.random().toString(36).substring(2, 8);
    setShareableLink(`${baseUrl}/#/shared/${randomId}`);
  }, [currentUser, navigate]);

  // Validate API key when changed with debounce
  useEffect(() => {
    if (!apiKey || apiKey.length < 10) return;
    
    const timer = setTimeout(() => {
      validateApiKey();
    }, 800);
    
    return () => clearTimeout(timer);
  }, [apiKey, provider]);

  const validateApiKey = async () => {
    if (!apiKey || apiKey.trim() === '') return;
    
    setValidating(true);
    try {
      // Simple validation request that doesn't create a session yet
      const response = await axios.post('/api/auth/validate_key', {
        provider: provider,
        api_key: apiKey
      });
      
      if (response.data.valid) {
        setError('');
        toast.success('API key is valid!');
      } else {
        setError('Invalid API key');
        toast.error('Invalid API key');
      }
    } catch (err) {
      console.error('Validation failed:', err);
      setError(err.response?.data?.error || err.message || 'API key validation failed');
    } finally {
      setValidating(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    
    try {
      console.log(`Logging in with ${provider} ${apiKey ? 'using provided key' : 'using default key'}`);
      
      const response = await axios.post('/api/auth/set_api_key', {
        provider: provider,
        api_key: apiKey || null,
      });
      
      if (response.data.token) {
        localStorage.setItem('token', response.data.token);
        axios.defaults.headers.common['Authorization'] = `Bearer ${response.data.token}`;
        
        // Update auth context with user information
        if (setCurrentUser && setAuthProvider) {
          setCurrentUser(response.data.user_id || 'user');
          setAuthProvider(provider);
        }
        
        toast.success('Successfully signed in!');
        
        // Force a small delay to ensure state updates
        setTimeout(() => {
          navigate('/profile');
        }, 100);
      } else {
        throw new Error('No token returned from server');
      }
    } catch (err) {
      console.error('Login failed:', err);
      setError(err.response?.data?.error || err.message || 'Failed to authenticate');
      toast.error('Login failed: ' + (err.response?.data?.error || err.message || 'Authentication error'));
    } finally {
      setLoading(false);
    }
  };

  const handleCopyShareLink = () => {
    navigator.clipboard.writeText(shareableLink);
    toast.success('Link copied to clipboard!');
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100 flex flex-col justify-center py-12 sm:px-6 lg:px-8">
      <div className="sm:mx-auto sm:w-full sm:max-w-md">
        <div className="flex justify-center">
          <div className="h-16 w-16 rounded-full bg-gradient-to-br from-harvard-crimson to-harvard-dark flex items-center justify-center text-white text-3xl shadow-lg">
            🎓
          </div>
        </div>
        <h2 className="mt-6 text-center text-3xl font-extrabold text-gray-900">
          ChatHarvard
        </h2>
        <p className="mt-2 text-center text-sm text-gray-600">
          Your Personal Academic Advisor for Harvard University
        </p>
      </div>

      <div className="mt-8 sm:mx-auto sm:w-full sm:max-w-md">
        <div className="bg-white py-8 px-4 shadow-xl sm:rounded-xl sm:px-10 border border-gray-100">
          <form onSubmit={handleSubmit} className="space-y-6">
            <div>
              <p className="text-sm font-medium text-gray-700 mb-4 text-center">
                Choose your AI provider
              </p>
              
              <div className="mt-4 space-y-4">
                <label className="block text-sm font-medium text-gray-700">Provider</label>
                <div className="mt-1 grid grid-cols-2 gap-3">
                  <button
                    type="button"
                    onClick={() => setProvider('openai')}
                    className={`flex justify-center items-center py-2 px-3 border ${
                      provider === 'openai' 
                        ? 'border-harvard-crimson bg-harvard-light text-harvard-crimson' 
                        : 'border-gray-300 bg-white text-gray-700'
                    } rounded-md shadow-sm text-sm font-medium focus:outline-none transition-all duration-150`}
                  >
                    OpenAI (GPT-4)
                  </button>
                  <button
                    type="button"
                    onClick={() => setProvider('anthropic')}
                    className={`flex justify-center items-center py-2 px-3 border ${
                      provider === 'anthropic' 
                        ? 'border-harvard-crimson bg-harvard-light text-harvard-crimson' 
                        : 'border-gray-300 bg-white text-gray-700'
                    } rounded-md shadow-sm text-sm font-medium focus:outline-none transition-all duration-150`}
                  >
                    Anthropic (Claude)
                  </button>
                </div>
                
                <div className="mt-3">
                  <label htmlFor="api-key" className="block text-sm font-medium text-gray-700">API Key (Optional)</label>
                  <div className="mt-1">
                    <div className="relative rounded-md shadow-sm">
                      <input
                        type="password"
                        id="api-key"
                        placeholder="Paste your API key or leave blank for default"
                        value={apiKey}
                        onChange={(e) => setApiKey(e.target.value)}
                        className={`w-full px-3 py-2 border ${error ? 'border-red-300' : 'border-gray-300'} rounded-md shadow-sm focus:ring-harvard-crimson focus:border-harvard-crimson sm:text-sm pr-10`}
                      />
                      {validating && (
                        <div className="absolute inset-y-0 right-0 pr-3 flex items-center">
                          <svg className="animate-spin h-5 w-5 text-gray-400" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                          </svg>
                        </div>
                      )}
                      {!validating && !error && apiKey && (
                        <div className="absolute inset-y-0 right-0 pr-3 flex items-center">
                          <svg className="h-5 w-5 text-green-500" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor">
                            <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.857-9.809a.75.75 0 00-1.214-.882l-3.483 4.79-1.88-1.88a.75.75 0 10-1.06 1.061l2.5 2.5a.75.75 0 001.137-.089l4-5.5z" clipRule="evenodd" />
                          </svg>
                        </div>
                      )}
                      {!validating && error && (
                        <div className="absolute inset-y-0 right-0 pr-3 flex items-center">
                          <svg className="h-5 w-5 text-red-500" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor">
                            <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.28 7.22a.75.75 0 00-1.06 1.06L8.94 10l-1.72 1.72a.75.75 0 101.06 1.06L10 11.06l1.72 1.72a.75.75 0 101.06-1.06L11.06 10l1.72-1.72a.75.75 0 00-1.06-1.06L10 8.94 8.28 7.22z" clipRule="evenodd" />
                          </svg>
                        </div>
                      )}
                    </div>
                  </div>
                  <p className="mt-1 text-xs text-gray-500">
                    Leave blank to use our default {provider} key
                  </p>
                </div>
                
                {error && (
                  <div className="rounded-md bg-red-50 p-4">
                    <div className="flex">
                      <div className="ml-3">
                        <h3 className="text-sm font-medium text-red-800">
                          {error}
                        </h3>
                      </div>
                    </div>
                  </div>
                )}
                
                <button
                  type="submit"
                  disabled={loading}
                  className="w-full flex justify-center items-center py-3 px-4 border border-transparent rounded-lg shadow-sm text-sm font-medium text-white bg-gradient-to-r from-harvard-crimson to-harvard-dark hover:from-harvard-dark hover:to-harvard-crimson focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-harvard-crimson transition-all duration-200"
                >
                  {loading ? (
                    <>
                      <svg className="animate-spin -ml-1 mr-2 h-4 w-4 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                      </svg>
                      Signing in...
                    </>
                  ) : 'Sign In'}
                </button>
              </div>
            </div>
          </form>

          <div className="mt-8">
            <div className="rounded-lg bg-gradient-to-r from-gray-50 to-gray-100 p-4 border border-gray-200">
              <div className="flex">
                <div className="flex-shrink-0">
                  <svg className="h-5 w-5 text-gray-400" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true">
                    <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-8-3a1 1 0 00-.867.5 1 1 0 11-1.731-1A3 3 0 0113 8a3.001 3.001 0 01-2 2.83V11a1 1 0 11-2 0v-1a1 1 0 011-1 1 1 0 100-2zm0 8a1 1 0 100-2 1 1 0 000 2z" clipRule="evenodd" />
                  </svg>
                </div>
                <div className="ml-3">
                  <p className="text-sm text-gray-700">
                    Sign in to access personalized academic recommendations based on your course history.
                  </p>
                </div>
              </div>
            </div>
          </div>

          <div className="mt-4 border-t border-gray-200 pt-4">
            <button
              type="button"
              onClick={() => setShowShareLink(!showShareLink)}
              className="text-sm text-harvard-crimson hover:text-harvard-dark font-medium"
            >
              {showShareLink ? "Hide sharing link" : "Share this app"}
            </button>
            
            {showShareLink && (
              <div className="mt-2">
                <div className="flex items-center gap-2">
                  <input
                    type="text"
                    readOnly
                    value={shareableLink}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm text-sm bg-gray-50"
                  />
                  <button
                    type="button"
                    onClick={handleCopyShareLink}
                    className="p-2 bg-harvard-light text-harvard-crimson rounded-md hover:bg-harvard-crimson hover:text-white transition-colors"
                  >
                    <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 5H6a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2v-1M8 5a2 2 0 002 2h2a2 2 0 002-2M8 5a2 2 0 012-2h2a2 2 0 012 2m0 0h2a2 2 0 012 2v3m2 4H10m0 0l3-3m-3 3l3 3" />
                    </svg>
                  </button>
                </div>
                <p className="mt-1 text-xs text-gray-500">
                  Share this link with others to let them try ChatHarvard
                </p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

export default Login;