import React, { createContext, useState, useEffect, useContext } from 'react';
import axios from 'axios';

const AuthContext = createContext();

export const useAuth = () => useContext(AuthContext);

export const AuthProvider = ({ children }) => {
  const [currentUser, setCurrentUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [authProvider, setAuthProvider] = useState('');

  useEffect(() => {
    // Add these debug logs in the checkUser function
const checkUser = async () => {
  try {
    const token = localStorage.getItem('token');
    console.log('Checking auth with token:', token ? 'exists' : 'none');
    
    if (token) {
      axios.defaults.headers.common['Authorization'] = `Bearer ${token}`;
      try {
        console.log('Verifying token...');
        const response = await axios.get('/api/auth/verify');
        console.log('Auth verify response:', response.data);
        
        if (response.data.authenticated) {
          setCurrentUser(response.data.user_id);
          setAuthProvider(response.data.auth_provider);
          console.log('User authenticated:', response.data.user_id);
        } else {
          console.log('Token invalid, clearing auth state');
          localStorage.removeItem('token');
          delete axios.defaults.headers.common['Authorization'];
        }
      } catch (verifyError) {
        console.error('Verify error:', verifyError);
        localStorage.removeItem('token');
        delete axios.defaults.headers.common['Authorization'];
      }
    } else {
      console.log('No token found');
    }
      } catch (error) {
        console.error('Auth error:', error);
        localStorage.removeItem('token');
        delete axios.defaults.headers.common['Authorization'];
      } finally {
        setLoading(false);
      }
    };

    checkUser();
  }, []);

  const login = async (provider) => {
    try {
      const response = await axios.get(`/auth/${provider}/login`);
      window.location.href = response.data.auth_url;
    } catch (error) {
      console.error('Login error:', error);
      throw error;
    }
  };

  const logout = async () => {
    try {
      await axios.post('/api/auth/logout');
      localStorage.removeItem('token');
      delete axios.defaults.headers.common['Authorization'];
      setCurrentUser(null);
      setAuthProvider('');
    } catch (error) {
      console.error('Logout error:', error);
      // Force logout even if API call fails
      localStorage.removeItem('token');
      delete axios.defaults.headers.common['Authorization'];
      setCurrentUser(null);
      setAuthProvider('');
    }
  };

  const handleAuthCallback = async (provider, code) => {
    try {
      const response = await axios.get(`/auth/${provider}/callback?code=${code}`);
      localStorage.setItem('token', response.data.token);
      axios.defaults.headers.common['Authorization'] = `Bearer ${response.data.token}`;
      
      const verifyResponse = await axios.get('/api/auth/verify');
      setCurrentUser(verifyResponse.data.user_id);
      setAuthProvider(verifyResponse.data.auth_provider);
      
      return response.data.redirect;
    } catch (error) {
      console.error('Auth callback error:', error);
      throw error;
    }
  };

  const value = {
    currentUser,
    authProvider,
    loading,
    login,
    logout,
    handleAuthCallback,
    setCurrentUser,  // Add these two functions to expose them
    setAuthProvider
  };

  return (
    <AuthContext.Provider value={value}>
      {!loading && children}
    </AuthContext.Provider>
  );
};

