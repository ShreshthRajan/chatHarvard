import React, { useState } from 'react';
import { Link, useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { Disclosure, Menu, Transition } from '@headlessui/react';
import { Bars3Icon, XMarkIcon, UserCircleIcon } from '@heroicons/react/24/outline';
import ThemeToggleButton from './ThemeToggleButton';

function classNames(...classes) {
  return classes.filter(Boolean).join(' ');
}

function Navbar() {
  const { currentUser, authProvider, logout } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  
  const handleLogout = async () => {
    await logout();
    navigate('/login');
  };
  
  const navigation = [
    { name: 'Profile', href: '/profile', current: location.pathname === '/profile' },
    { name: 'Chat', href: '/', current: location.pathname === '/' },
  ];

  return (
    <Disclosure as="nav" className="bg-white dark:bg-dark-100 backdrop-blur-sm bg-opacity-90 dark:bg-opacity-95 sticky top-0 z-50 shadow-sm border-b border-gray-200 dark:border-dark-300">
      {({ open }) => (
        <>
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="flex justify-between h-16">
              <div className="flex">
                <div className="flex-shrink-0 flex items-center">
                  <span className="text-2xl">🎓</span>
                  <span className="ml-2 text-xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-harvard-crimson to-harvard-dark dark:from-accent-primary dark:to-accent-tertiary">ChatHarvard</span>
                </div>
                <div className="hidden sm:ml-6 sm:flex sm:space-x-8">
                  {navigation.map((item) => (
                    <Link
                      key={item.name}
                      to={item.href}
                      className={classNames(
                        item.current
                          ? 'border-harvard-crimson dark:border-accent-primary text-gray-900 dark:text-dark-800 font-medium'
                          : 'border-transparent text-gray-500 dark:text-dark-600 hover:text-gray-700 dark:hover:text-dark-700 hover:border-gray-300 dark:hover:border-dark-500',
                        'inline-flex items-center px-1 pt-1 border-b-2 text-sm transition-all duration-150'
                      )}
                      aria-current={item.current ? 'page' : undefined}
                    >
                      {item.name}
                    </Link>
                  ))}
                </div>
              </div>
              <div className="hidden sm:ml-6 sm:flex sm:items-center space-x-3">
                {/* Theme Toggle Button */}
                <ThemeToggleButton />
                
                {/* Provider badge */}
                <span className="bg-gradient-to-r from-gray-50 to-gray-100 dark:from-dark-200 dark:to-dark-300 text-gray-800 dark:text-dark-700 text-xs font-medium px-3 py-1 rounded-full border border-gray-200 dark:border-dark-400 flex items-center">
                  <div className={`w-2 h-2 rounded-full mr-1.5 ${authProvider === 'anthropic' ? 'bg-purple-500' : 'bg-green-500'}`}></div>
                  {authProvider === 'anthropic' ? 'Anthropic' : 'OpenAI'}
                </span>
                
                {/* Profile dropdown */}
                <Menu as="div" className="ml-3 relative">
                  <div>
                    <Menu.Button className="flex text-sm rounded-full focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-harvard-crimson dark:focus:ring-accent-primary dark:focus:ring-offset-dark-200 bg-gray-100 dark:bg-dark-300 p-1 hover:bg-gray-200 dark:hover:bg-dark-400 transition-colors duration-150">
                      <span className="sr-only">Open user menu</span>
                      <UserCircleIcon className="h-7 w-7 text-gray-600 dark:text-dark-600" />
                    </Menu.Button>
                  </div>
                  <Transition
                    as={React.Fragment}
                    enter="transition ease-out duration-200"
                    enterFrom="transform opacity-0 scale-95"
                    enterTo="transform opacity-100 scale-100"
                    leave="transition ease-in duration-75"
                    leaveFrom="transform opacity-100 scale-100"
                    leaveTo="transform opacity-0 scale-95"
                  >
                    <Menu.Items className="origin-top-right absolute right-0 mt-2 w-48 rounded-md shadow-lg dark:shadow-dropdown-dark py-1 bg-white dark:bg-dark-200 ring-1 ring-black ring-opacity-5 dark:ring-dark-400 focus:outline-none divide-y divide-gray-100 dark:divide-dark-400">
                      <div className="px-4 py-3">
                        <p className="text-sm text-gray-900 dark:text-dark-800 font-medium">Harvard Student</p>
                        <p className="text-xs text-gray-500 dark:text-dark-600 truncate">Connected via {authProvider === 'anthropic' ? 'Anthropic' : 'OpenAI'}</p>
                      </div>
                      <div className="py-1">
                        <Menu.Item>
                          {({ active }) => (
                            <Link
                              to="/profile"
                              className={classNames(
                                active ? 'bg-gray-50 dark:bg-dark-300' : '',
                                'flex items-center px-4 py-2 text-sm text-gray-700 dark:text-dark-700'
                              )}
                            >
                              <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4 mr-2 text-gray-500 dark:text-dark-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                              </svg>
                              Your Profile
                            </Link>
                          )}
                        </Menu.Item>
                        <Menu.Item>
                          {({ active }) => (
                            <button
                              onClick={handleLogout}
                              className={classNames(
                                active ? 'bg-gray-50 dark:bg-dark-300' : '',
                                'flex w-full items-center text-left px-4 py-2 text-sm text-gray-700 dark:text-dark-700'
                              )}
                            >
                              <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4 mr-2 text-gray-500 dark:text-dark-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />
                              </svg>
                              Sign out
                            </button>
                          )}
                        </Menu.Item>
                      </div>
                    </Menu.Items>
                  </Transition>
                </Menu>
              </div>
              
              {/* Mobile menu button */}
              <div className="-mr-2 flex items-center sm:hidden space-x-1">
                <ThemeToggleButton />
                
                <Disclosure.Button className="inline-flex items-center justify-center p-2 rounded-md text-gray-400 dark:text-dark-600 hover:text-gray-500 dark:hover:text-dark-700 hover:bg-gray-100 dark:hover:bg-dark-300 focus:outline-none focus:ring-2 focus:ring-inset focus:ring-harvard-crimson dark:focus:ring-accent-primary">
                  <span className="sr-only">Open main menu</span>
                  {open ? (
                    <XMarkIcon className="block h-6 w-6" aria-hidden="true" />
                  ) : (
                    <Bars3Icon className="block h-6 w-6" aria-hidden="true" />
                  )}
                </Disclosure.Button>
              </div>
            </div>
          </div>

          {/* Mobile menu panel */}
          <Disclosure.Panel className="sm:hidden">
            <div className="pt-2 pb-3 space-y-1">
              {navigation.map((item) => (
                <Disclosure.Button
                  key={item.name}
                  as={Link}
                  to={item.href}
                  className={classNames(
                    item.current
                      ? 'bg-harvard-light dark:bg-dark-300 border-harvard-crimson dark:border-accent-primary text-harvard-crimson dark:text-accent-secondary'
                      : 'border-transparent text-gray-600 dark:text-dark-600 hover:bg-gray-50 dark:hover:bg-dark-300 hover:border-gray-300 dark:hover:border-dark-500 hover:text-gray-800 dark:hover:text-dark-700',
                    'block pl-3 pr-4 py-2 border-l-4 text-base font-medium transition-colors duration-150'
                  )}
                  aria-current={item.current ? 'page' : undefined}
                >
                  {item.name}
                </Disclosure.Button>
              ))}
              <div className="border-t border-gray-200 dark:border-dark-400 pt-2 pb-1">
                <div className="flex items-center px-4">
                  <div className="flex-shrink-0">
                    <UserCircleIcon className="h-8 w-8 text-gray-600 dark:text-dark-600" />
                  </div>
                  <div className="ml-3">
                    <div className="text-sm font-medium text-gray-800 dark:text-dark-800">Harvard Student</div>
                    <div className="text-xs text-gray-500 dark:text-dark-600">
                      <span className="inline-flex items-center bg-gradient-to-r from-gray-50 to-gray-100 dark:from-dark-200 dark:to-dark-300 px-2 py-0.5 rounded-full text-xs mt-0.5">
                        <div className={`w-1.5 h-1.5 rounded-full mr-1 ${authProvider === 'anthropic' ? 'bg-purple-500' : 'bg-green-500'}`}></div>
                        {authProvider === 'anthropic' ? 'Anthropic' : 'OpenAI'}
                      </span>
                    </div>
                  </div>
                </div>
                <div className="mt-3 space-y-1">
                  <button
                    onClick={handleLogout}
                    className="block w-full text-left px-4 py-2 text-base font-medium text-gray-600 dark:text-dark-600 hover:text-gray-800 dark:hover:text-dark-700 hover:bg-gray-50 dark:hover:bg-dark-300"
                  >
                    Sign out
                  </button>
                </div>
              </div>
            </div>
          </Disclosure.Panel>
        </>
      )}
    </Disclosure>
  );
}

export default Navbar;