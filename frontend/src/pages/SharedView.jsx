import React, { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import axios from 'axios';
import { toast } from 'react-hot-toast';

function SharedView() {
  const { shareId } = useParams();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [sharedData, setSharedData] = useState(null);

  useEffect(() => {
    const fetchSharedData = async () => {
      try {
        const response = await axios.get(`/api/shared/${shareId}`);
        setSharedData(response.data);
      } catch (err) {
        console.error('Error fetching shared data:', err);
        setError('Failed to load shared content. The link may be invalid or expired.');
        toast.error('Failed to load shared content');
      } finally {
        setLoading(false);
      }
    };

    fetchSharedData();
  }, [shareId]);

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex flex-col items-center justify-center p-4">
        <div className="flex flex-col items-center space-y-4">
          <div className="h-16 w-16 rounded-full bg-gradient-to-br from-harvard-crimson to-harvard-dark flex items-center justify-center text-white text-3xl shadow-lg">
            🎓
          </div>
          <h2 className="text-xl font-semibold text-gray-800">Loading ChatHarvard Profile...</h2>
          <div className="animate-spin rounded-full h-8 w-8 border-t-2 border-b-2 border-harvard-crimson"></div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gray-50 flex flex-col items-center justify-center p-4">
        <div className="max-w-md bg-white shadow-xl rounded-lg p-6 text-center">
          <div className="h-16 w-16 mx-auto rounded-full bg-red-100 flex items-center justify-center text-red-500 text-3xl mb-4">
            <svg xmlns="http://www.w3.org/2000/svg" className="h-8 w-8" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          </div>
          <h2 className="text-xl font-semibold text-gray-800 mb-2">Error Loading Profile</h2>
          <p className="text-gray-600 mb-4">{error}</p>
          <Link to="/login" className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-harvard-crimson hover:bg-harvard-dark focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-harvard-crimson">
            Go to Login
          </Link>
        </div>
      </div>
    );
  }

  const { profile, chatHistory } = sharedData;

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-white shadow">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4 flex items-center justify-between">
          <div className="flex items-center">
            <div className="h-10 w-10 rounded-full bg-gradient-to-br from-harvard-crimson to-harvard-dark flex items-center justify-center text-white mr-3">
              🎓
            </div>
            <h1 className="text-xl font-bold text-gray-900">ChatHarvard</h1>
          </div>
          <div>
            <Link to="/login" className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-harvard-crimson hover:bg-harvard-dark focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-harvard-crimson">
              Try it yourself
            </Link>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
        <div className="px-4 py-6 sm:px-0">
          <div className="border-b border-gray-200 pb-5 mb-5">
            <h3 className="text-lg leading-6 font-medium text-gray-900">
              Shared Academic Profile
            </h3>
            <p className="mt-2 max-w-4xl text-sm text-gray-500">
              This is a read-only view of a ChatHarvard profile that was shared with you.
            </p>
          </div>

          <div className="bg-white shadow overflow-hidden sm:rounded-lg mb-6">
            <div className="px-4 py-5 sm:px-6">
              <h3 className="text-lg leading-6 font-medium text-gray-900">
                Student Information
              </h3>
              <p className="mt-1 max-w-2xl text-sm text-gray-500">
                Academic details and course history.
              </p>
            </div>
            <div className="border-t border-gray-200">
              <dl>
                <div className="bg-gray-50 px-4 py-5 sm:grid sm:grid-cols-3 sm:gap-4 sm:px-6">
                  <dt className="text-sm font-medium text-gray-500">Concentration</dt>
                  <dd className="mt-1 text-sm text-gray-900 sm:mt-0 sm:col-span-2">{profile.concentration}</dd>
                </div>
                <div className="bg-white px-4 py-5 sm:grid sm:grid-cols-3 sm:gap-4 sm:px-6">
                  <dt className="text-sm font-medium text-gray-500">Year</dt>
                  <dd className="mt-1 text-sm text-gray-900 sm:mt-0 sm:col-span-2">{profile.year}</dd>
                </div>
                <div className="bg-gray-50 px-4 py-5 sm:grid sm:grid-cols-3 sm:gap-4 sm:px-6">
                  <dt className="text-sm font-medium text-gray-500">Courses Taken</dt>
                  <dd className="mt-1 text-sm text-gray-900 sm:mt-0 sm:col-span-2">
                    <div className="flex flex-wrap gap-2">
                      {profile.courses_taken.map((course) => (
                        <span key={course} className="inline-flex items-center px-3 py-0.5 rounded-full text-sm font-medium bg-harvard-light text-harvard-crimson">
                          {course}
                        </span>
                      ))}
                    </div>
                  </dd>
                </div>
                <div className="bg-white px-4 py-5 sm:grid sm:grid-cols-3 sm:gap-4 sm:px-6">
                  <dt className="text-sm font-medium text-gray-500">Academic Interests</dt>
                  <dd className="mt-1 text-sm text-gray-900 sm:mt-0 sm:col-span-2">
                    <div className="flex flex-wrap gap-2">
                      {profile.interests.map((interest) => (
                        <span key={interest} className="inline-flex items-center px-3 py-0.5 rounded-full text-sm font-medium bg-blue-100 text-blue-800">
                          {interest}
                        </span>
                      ))}
                    </div>
                  </dd>
                </div>
              </dl>
            </div>
          </div>

          {chatHistory && chatHistory.length > 0 && (
            <div className="bg-white shadow sm:rounded-lg">
              <div className="px-4 py-5 sm:px-6">
                <h3 className="text-lg leading-6 font-medium text-gray-900">
                  Sample Conversation
                </h3>
                <p className="mt-1 max-w-2xl text-sm text-gray-500">
                  See how ChatHarvard provides personalized academic advice.
                </p>
              </div>
              <div className="border-t border-gray-200">
                <div className="px-4 py-5 sm:p-6">
                  <div className="space-y-6">
                    {chatHistory.map((message, index) => (
                      <div key={index} className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                        <div className={`max-w-lg rounded-lg px-4 py-3 ${
                          message.role === 'user' 
                            ? 'bg-harvard-light text-harvard-dark' 
                            : 'bg-gray-100 text-gray-800'
                        }`}>
                          <div className="text-sm" style={{ whiteSpace: 'pre-wrap' }}>
                            {message.content}
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            </div>
          )}

          <div className="mt-12 text-center">
            <p className="text-base text-gray-500 mb-4">
              Want to create your own academic advisor?
            </p>
            <Link
              to="/login"
              className="inline-flex items-center px-6 py-3 border border-transparent text-base font-medium rounded-md shadow-sm text-white bg-harvard-crimson hover:bg-harvard-dark focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-harvard-crimson"
            >
              Get Started with ChatHarvard
            </Link>
          </div>
        </div>
      </main>
    </div>
  );
}

export default SharedView;

