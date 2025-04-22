import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Cog6ToothIcon, InformationCircleIcon, ArrowRightOnRectangleIcon } from '@heroicons/react/24/outline';

const Header = () => {
  const [settingsOpen, setSettingsOpen] = useState(false);
  const navigate = useNavigate();

  const handleLogout = () => {
    localStorage.removeItem('token');
    navigate('/login');
  };
  
  return (
    <header className="bg-dark-100 border-b border-dark-300 py-3 px-4">
      <div className="max-w-5xl mx-auto flex items-center justify-between">
        <div className="flex items-center space-x-4">
          <Link to="/" className="text-lg font-medium text-dark-800 flex items-center">
            <span className="text-accent-primary mr-2">🎓</span>
            ChatHarvard
          </Link>
          <div className="h-5 border-r border-dark-300 mx-1"></div>
          <nav className="flex space-x-4">
            <Link 
              to="/" 
              className={`px-1 py-1 border-b-2 ${
                window.location.hash === '#/' || window.location.hash === ''
                  ? 'border-accent-primary text-dark-800 font-medium'
                  : 'border-transparent text-dark-600 hover:text-dark-800'
              }`}
            >
              Chat
            </Link>
            <Link 
              to="/profile" 
              className={`px-1 py-1 border-b-2 ${
                window.location.hash === '#/profile'
                  ? 'border-accent-primary text-dark-800 font-medium'
                  : 'border-transparent text-dark-600 hover:text-dark-800'
              }`}
            >
              Profile
            </Link>
          </nav>
        </div>
        <div className="flex items-center">
          <button 
            onClick={() => setSettingsOpen(!settingsOpen)}
            className="p-2 rounded-full hover:bg-dark-200 text-dark-600"
          >
            <Cog6ToothIcon className="h-5 w-5" />
          </button>

          {/* Settings dropdown */}
          {settingsOpen && (
            <div className="absolute right-4 top-12 mt-2 w-48 rounded-md shadow-lg bg-white dark:bg-dark-200 ring-1 ring-black ring-opacity-5 z-50">
              <div className="py-1" role="menu" aria-orientation="vertical">
                <button
                  onClick={handleLogout}
                  className="w-full text-left px-4 py-2 text-sm text-gray-700 dark:text-dark-700 hover:bg-gray-100 dark:hover:bg-dark-300 flex items-center"
                  role="menuitem"
                >
                  <ArrowRightOnRectangleIcon className="h-4 w-4 mr-2" />
                  Log out
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </header>
  );
};

export default Header;