import React, { createContext, useState, useEffect, useContext } from 'react';
import axios from 'axios';

const AuthContext = createContext();

export const useAuth = () => useContext(AuthContext);

export const AuthProvider = ({ children }) => {
  const [currentUser, setCurrentUser] = useState(null);
  const [googleUser, setGoogleUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [authProvider, setAuthProvider] = useState('');

  useEffect(() => {
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
              
              // Set Google user if available
              if (response.data.google_user) {
                setGoogleUser(response.data.google_user);
              }
              
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

  const logout = async () => {
    try {
      await axios.post('/api/auth/logout');
      localStorage.removeItem('token');
      delete axios.defaults.headers.common['Authorization'];
      setCurrentUser(null);
      setAuthProvider('');
      setGoogleUser(null);
      
      // Also sign out from Google if user was signed in
      if (window.google && window.google.accounts) {
        window.google.accounts.id.disableAutoSelect();
      }
    } catch (error) {
      console.error('Logout error:', error);
      // Force logout even if API call fails
      localStorage.removeItem('token');
      delete axios.defaults.headers.common['Authorization'];
      setCurrentUser(null);
      setAuthProvider('');
      setGoogleUser(null);
    }
  };

  // New function to handle Google credential response
  const handleGoogleLogin = async (credential) => {
    try {
      const response = await axios.post('/api/auth/google-verify', { credential });
      
      if (response.data.success) {
        setGoogleUser(response.data.user);
        return response.data.user;
      } else {
        throw new Error(response.data.message || 'Google verification failed');
      }
    } catch (error) {
      console.error('Google verification error:', error);
      throw error;
    }
  };

  const value = {
    currentUser,
    googleUser,
    authProvider,
    loading,
    logout,
    handleGoogleLogin,
    setCurrentUser,
    setAuthProvider,
    setGoogleUser
  };

  return (
    <AuthContext.Provider value={value}>
      {!loading && children}
    </AuthContext.Provider>
  );
};