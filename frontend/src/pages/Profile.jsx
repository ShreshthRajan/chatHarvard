import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import Navbar from '../components/Navbar';

function Profile() {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [concentrations, setConcentrations] = useState([]);
  
  const [profile, setProfile] = useState({
    concentration: '',
    year: '',
    courses_taken: [],
    interests: [],
    learning_preferences: []
  });
  
  // Form input state
  const [courseInput, setCourseInput] = useState('');
  const [selectedInterests, setSelectedInterests] = useState([]);
  const [selectedPreferences, setSelectedPreferences] = useState([]);
  
  useEffect(() => {
    const fetchProfile = async () => {
      try {
        const profileResponse = await axios.get('/api/profile');
        setProfile(profileResponse.data);
        
        if (profileResponse.data.interests) {
          setSelectedInterests(profileResponse.data.interests);
        }
        
        if (profileResponse.data.learning_preferences) {
          setSelectedPreferences(profileResponse.data.learning_preferences);
        }
        
        const concentrationsResponse = await axios.get('/api/concentrations');
        setConcentrations(concentrationsResponse.data);
      } catch (error) {
        console.error('Error fetching profile:', error);
      } finally {
        setLoading(false);
      }
    };
    
    fetchProfile();
  }, []);
  
  const handleChange = (e) => {
    const { name, value } = e.target;
    setProfile({ ...profile, [name]: value });
  };
  
  const handleAddCourse = () => {
    if (courseInput.trim()) {
      setProfile({
        ...profile,
        courses_taken: [...profile.courses_taken, courseInput.trim()]
      });
      setCourseInput('');
    }
  };
  
  const handleRemoveCourse = (index) => {
    const updatedCourses = [...profile.courses_taken];
    updatedCourses.splice(index, 1);
    setProfile({ ...profile, courses_taken: updatedCourses });
  };
  
  const toggleInterest = (interest) => {
    const updatedInterests = selectedInterests.includes(interest)
      ? selectedInterests.filter(i => i !== interest)
      : [...selectedInterests, interest];
    
    setSelectedInterests(updatedInterests);
    setProfile({ ...profile, interests: updatedInterests });
  };
  
  const togglePreference = (preference) => {
    const updatedPreferences = selectedPreferences.includes(preference)
      ? selectedPreferences.filter(p => p !== preference)
      : [...selectedPreferences, preference];
    
    setSelectedPreferences(updatedPreferences);
    setProfile({ ...profile, learning_preferences: updatedPreferences });
  };
  
  const handleSubmit = async (e) => {
    e.preventDefault();
    setSaving(true);
    
    try {
      await axios.post('/api/profile', profile);
      navigate('/');
    } catch (error) {
      console.error('Error saving profile:', error);
      alert('Failed to save profile. Please try again.');
    } finally {
      setSaving(false);
    }
  };
  
  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex justify-center items-center">
        <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-harvard-crimson"></div>
      </div>
    );
  }
  
  const interestOptions = [
    "Mathematics", "Computer Science", "Data Science", "Economics", "Business", 
    "History", "Literature", "Philosophy", "Physics", "Chemistry", "Biology",
    "Psychology", "Sociology", "Political Science", "International Relations",
    "Arts", "Music", "Film", "Environmental Studies", "Public Health"
  ];
  
  const learningOptions = [
    "Lectures", "Seminars", "Project-based", "Lab work", "Reading-intensive",
    "Writing-intensive", "Discussion-based", "Problem sets", "Research-oriented"
  ];
  
  const yearOptions = ["Freshman", "Sophomore", "Junior", "Senior"];
  
  return (
    <>
      <Navbar />
      <div className="min-h-screen bg-gradient-to-b from-gray-50 to-white py-12 px-4 sm:px-6 lg:px-8">
        <div className="max-w-3xl mx-auto">
          <div className="flex items-center justify-center mb-8">
            <h1 className="text-3xl font-bold text-gray-900 text-center">Academic Profile</h1>
            <div className="ml-2 px-3 py-1 text-xs font-medium rounded-full bg-harvard-light text-harvard-crimson border border-harvard-crimson border-opacity-20">
              Personalizes Your Advisor
            </div>
          </div>
          
          <div className="bg-white shadow-card overflow-hidden sm:rounded-xl border border-gray-100">
            <div className="px-4 py-6 sm:p-8">
              <form onSubmit={handleSubmit}>
                <div className="grid grid-cols-1 gap-y-6 gap-x-4 sm:grid-cols-6">
                  {/* Concentration with enhanced styling */}
                  <div className="sm:col-span-3">
                    <label htmlFor="concentration" className="block text-sm font-medium text-gray-700 mb-1">
                      Concentration
                    </label>
                    <select
                      id="concentration"
                      name="concentration"
                      value={profile.concentration}
                      onChange={handleChange}
                      required
                      className="mt-1 block w-full bg-gray-50 border border-gray-300 rounded-lg shadow-sm py-2.5 px-3 focus:outline-none focus:ring-harvard-crimson focus:border-harvard-crimson sm:text-sm transition-all duration-150"
                    >
                      <option value="">Select a concentration</option>
                      {concentrations.map((conc) => (
                        <option key={conc} value={conc}>{conc}</option>
                      ))}
                    </select>
                  </div>
                  
                  {/* Year with enhanced styling */}
                  <div className="sm:col-span-3">
                    <label htmlFor="year" className="block text-sm font-medium text-gray-700 mb-1">
                      Year
                    </label>
                    <select
                      id="year"
                      name="year"
                      value={profile.year}
                      onChange={handleChange}
                      required
                      className="mt-1 block w-full bg-gray-50 border border-gray-300 rounded-lg shadow-sm py-2.5 px-3 focus:outline-none focus:ring-harvard-crimson focus:border-harvard-crimson sm:text-sm transition-all duration-150"
                    >
                      <option value="">Select your year</option>
                      {yearOptions.map((year) => (
                        <option key={year} value={year}>{year}</option>
                      ))}
                    </select>
                  </div>
                  
                  {/* Courses Taken with enhanced styling */}
                  <div className="sm:col-span-6">
                    <label htmlFor="courses" className="block text-sm font-medium text-gray-700 mb-1">
                      Courses You've Taken
                    </label>
                    <div className="mt-1 flex rounded-md shadow-sm">
                      <input
                        type="text"
                        name="courses"
                        id="courses"
                        value={courseInput}
                        onChange={(e) => setCourseInput(e.target.value)}
                        placeholder="e.g., MATH 55, CS 50"
                        className="flex-1 min-w-0 block w-full px-3 py-3 rounded-l-lg border border-gray-300 bg-gray-50 focus:outline-none focus:ring-harvard-crimson focus:border-harvard-crimson sm:text-sm transition-all duration-150"
                      />
                      <button
                        type="button"
                        onClick={handleAddCourse}
                        className="inline-flex items-center px-4 py-3 border border-transparent rounded-r-lg shadow-sm text-sm font-medium text-white bg-harvard-crimson hover:bg-harvard-dark focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-harvard-crimson transition-colors"
                      >
                        Add
                      </button>
                    </div>
                    
                    {/* Courses List with enhanced styling */}
                    {profile.courses_taken.length > 0 && (
                      <div className="mt-3 p-3 bg-gray-50 rounded-lg border border-gray-200">
                        <div className="text-xs font-medium text-gray-500 mb-2">Your Courses:</div>
                        <div className="flex flex-wrap gap-2">
                          {profile.courses_taken.map((course, index) => (
                            <span key={index} className="inline-flex rounded-full items-center py-1 pl-3 pr-1.5 text-sm font-medium bg-white border border-gray-200 text-gray-800 shadow-sm">
                              {course}
                              <button
                                type="button"
                                onClick={() => handleRemoveCourse(index)}
                                className="flex-shrink-0 ml-1 h-4 w-4 rounded-full inline-flex items-center justify-center text-gray-400 hover:bg-gray-200 hover:text-gray-500 focus:outline-none focus:bg-gray-500 focus:text-white transition-colors"
                              >
                                <span className="sr-only">Remove {course}</span>
                                <svg className="h-2 w-2" stroke="currentColor" fill="none" viewBox="0 0 8 8">
                                  <path strokeLinecap="round" strokeWidth="1.5" d="M1 1l6 6m0-6L1 7" />
                                </svg>
                              </button>
                            </span>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                  
                  {/* Academic Interests with enhanced styling */}
                  <div className="sm:col-span-6">
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Academic Interests
                    </label>
                    <div className="mt-1 bg-gray-50 p-3 rounded-lg border border-gray-200">
                      <div className="flex flex-wrap gap-2">
                        {interestOptions.map((interest) => (
                          <button
                            key={interest}
                            type="button"
                            onClick={() => toggleInterest(interest)}
                            className={`inline-flex items-center px-3 py-1.5 rounded-full text-sm font-medium transition-all duration-150
                              ${selectedInterests.includes(interest) 
                                ? 'bg-harvard-crimson text-white shadow-sm' 
                                : 'bg-white border border-gray-200 text-gray-700 hover:bg-gray-100 shadow-sm'
                              }`}
                          >
                            {interest}
                          </button>
                        ))}
                      </div>
                    </div>
                  </div>
                  
                  {/* Learning Preferences with enhanced styling */}
                  <div className="sm:col-span-6">
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Learning Preferences
                    </label>
                    <div className="mt-1 bg-gray-50 p-3 rounded-lg border border-gray-200">
                      <div className="flex flex-wrap gap-2">
                        {learningOptions.map((preference) => (
                          <button
                          key={preference}
                          type="button"
                          onClick={() => togglePreference(preference)}
                          className={`inline-flex items-center px-3 py-1.5 rounded-full text-sm font-medium transition-all duration-150
                            ${selectedPreferences.includes(preference) 
                              ? 'bg-harvard-crimson text-white shadow-sm' 
                              : 'bg-white border border-gray-200 text-gray-700 hover:bg-gray-100 shadow-sm'
                            }`}
                        >
                          {preference}
                        </button>
                      ))}
                    </div>
                  </div>
                </div>
              </div>
              
              <div className="pt-8 flex justify-end">
                <button
                  type="submit"
                  disabled={saving}
                  className="inline-flex items-center px-5 py-2.5 border border-transparent rounded-lg shadow-sm text-sm font-medium text-white bg-gradient-to-r from-harvard-crimson to-harvard-dark hover:from-harvard-dark hover:to-harvard-crimson focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-harvard-crimson transition-all duration-200"
                >
                  {saving ? (
                    <>
                      <svg className="animate-spin -ml-1 mr-2 h-4 w-4 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                      </svg>
                      Saving...
                    </>
                  ) : (
                    'Save Profile'
                  )}
                </button>
              </div>
            </form>
          </div>
          <div className="bg-gray-50 px-4 py-4 sm:px-8 border-t border-gray-200">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 text-harvard-crimson" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              </div>
              <div className="ml-3">
                <p className="text-sm text-gray-600">
                  The more details you provide, the better ChatHarvard can personalize course recommendations and academic advice.
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </>
);
}

export default Profile;