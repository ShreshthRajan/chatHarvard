import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import Navbar from '../components/Navbar';
import FileUpload from '../components/FileUpload';
import { useToast } from '../context/ToastContext';

function Profile() {
  const navigate = useNavigate();
  const { showToast } = useToast();
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [concentrations, setConcentrations] = useState([]);
  const [uploadLoading, setUploadLoading] = useState(false);
  const [pasteModalOpen, setPasteModalOpen] = useState(false);
  const [coursePasteText, setCoursePasteText] = useState('');
  const [modalTab, setModalTab] = useState('paste'); // 'paste' or 'upload'
  
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
        showToast('Failed to load profile data', 'error');
      } finally {
        setLoading(false);
      }
    };
    
    fetchProfile();
  }, [showToast]);
  
  const handleChange = (e) => {
    const { name, value } = e.target;
    setProfile({ ...profile, [name]: value });
  };
  
  // Fixed function to properly handle course input
  const handleAddCourse = (e) => {
    // Prevent default form submission behavior
    if (e) e.preventDefault();
    
    if (courseInput.trim()) {
      // Format course code to uppercase if it contains letters
      const formattedInput = courseInput.trim().replace(/([a-zA-Z]+)\s*(\d+[a-zA-Z]*)/i, (_, dept, num) => {
        return `${dept.toUpperCase()} ${num}`;
      });
      
      // Directly update the profile state with the new course
      const updatedCourses = [...profile.courses_taken];
      
      // Check if course already exists to avoid duplicates
      if (!updatedCourses.includes(formattedInput)) {
        updatedCourses.push(formattedInput);
        
        // Update profile with the new courses array
        setProfile({
          ...profile,
          courses_taken: updatedCourses
        });
        
        // Log for debugging
        console.log('Added course:', formattedInput);
        console.log('Updated courses:', updatedCourses);
      }
      
      // Clear the input field
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
      showToast('Profile saved successfully', 'success');
      navigate('/');
    } catch (error) {
      console.error('Error saving profile:', error);
      showToast('Failed to save profile', 'error');
    } finally {
      setSaving(false);
    }
  };
  
  const handlePdfUpload = async (file) => {
    setUploadLoading(true);
    
    try {
      const formData = new FormData();
      formData.append('pdf', file);
      
      const response = await axios.post('/api/extract_courses', formData, {
        headers: {
          'Content-Type': 'multipart/form-data'
        }
      });
      
      const extractedCourses = response.data.courses || [];
      
      if (extractedCourses.length === 0) {
        showToast('No courses found in the PDF', 'warning');
      } else {
        // Combine existing courses with new ones, avoiding duplicates
        const existingCourseCodes = new Set(profile.courses_taken);
        const newCourses = extractedCourses.filter(course => !existingCourseCodes.has(course));
        
        setProfile({
          ...profile,
          courses_taken: [...profile.courses_taken, ...newCourses]
        });
        
        showToast(`Added ${newCourses.length} courses from PDF`, 'success');
        setPasteModalOpen(false);
      }
    } catch (error) {
      console.error('Error extracting courses from PDF:', error);
      showToast('Failed to extract courses from PDF', 'error');
    } finally {
      setUploadLoading(false);
    }
  };
  
  const handlePasteExtract = () => {
    if (!coursePasteText.trim()) {
      showToast('Please paste some text containing course codes', 'warning');
      return;
    }
    
    // Regular expression to match common course code formats
    // This regex looks for patterns like "CS 50", "MATH 21A", etc.
    const coursePattern = /([A-Za-z]{2,4})\s*(\d{1,3}[A-Za-z]{0,2})/g;
    const matches = [...coursePasteText.matchAll(coursePattern)];
    
    if (matches.length === 0) {
      showToast('No recognizable course codes found', 'warning');
      return;
    }
    
    // Format the matches and check for duplicates
    const existingCourseCodes = new Set(profile.courses_taken);
    const newCourses = [];
    
    matches.forEach(match => {
      const courseCode = `${match[1].toUpperCase()} ${match[2]}`;
      if (!existingCourseCodes.has(courseCode)) {
        newCourses.push(courseCode);
        existingCourseCodes.add(courseCode);
      }
    });
    
    if (newCourses.length === 0) {
      showToast('All found courses are already in your list', 'info');
    } else {
      setProfile({
        ...profile,
        courses_taken: [...profile.courses_taken, ...newCourses]
      });
      
      showToast(`Added ${newCourses.length} courses from text`, 'success');
      setCoursePasteText('');
      setPasteModalOpen(false);
    }
  };
  
  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 dark:bg-dark-100 flex justify-center items-center transition-colors">
        <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-accent-primary"></div>
      </div>
    );
  }
  
  const interestOptions = [
    "Anthropology",
    "Art History",
    "Arts",
    "Biology",
    "Business",
    "Finance",
    "Chemistry",
    "Computer Science", 
    "Data Science",
    "Education",
    "Economics",
    "Environmental Studies",
    "Film and Visual Studies",
    "Gender Studies",
    "Government",
    "History",
    "International Relations",
    "Literature",
    "Mathematics",
    "Music",
    "Neuroscience",
    "Public Policy",
    "Philosophy",
    "Physics",
    "Psychology",
    "Public Health",
    "Sociology",
    "South Asian Studies"
  ];
  
  const learningOptions = [
    "Lectures", "Seminars", "Project-based", "Lab work", "Reading-intensive",
    "Writing-intensive", "Discussion-based", "Problem sets", "Research-oriented"
  ];
  
  const yearOptions = ["Freshman", "Sophomore", "Junior", "Senior"];
  
  return (
    <>
      <Navbar />
      <div className="min-h-screen bg-gray-50 dark:bg-dark-100 py-12 px-4 sm:px-6 lg:px-8 transition-colors">
        <div className="max-w-3xl mx-auto">
          <div className="flex items-center justify-center mb-8">
            <h1 className="text-3xl font-bold text-gray-900 dark:text-dark-800 text-center">Academic Profile</h1>
            <div className="ml-2 px-3 py-1 text-xs font-medium rounded-full bg-accent-primary bg-opacity-10 text-accent-primary border border-accent-primary border-opacity-20 dark:bg-dark-300 dark:text-accent-secondary dark:border-accent-primary">
              Personalizes Your Advisor
            </div>
          </div>
          
          <div className="bg-white dark:bg-dark-200 shadow-card dark:shadow-card-dark overflow-hidden sm:rounded-xl border border-gray-100 dark:border-dark-300 transition-colors">
            <div className="px-4 py-6 sm:p-8">
              <form onSubmit={handleSubmit}>
                <div className="grid grid-cols-1 gap-y-6 gap-x-4 sm:grid-cols-6">
                  {/* Concentration with enhanced styling */}
                  <div className="sm:col-span-3">
                    <label htmlFor="concentration" className="block text-sm font-medium text-gray-700 dark:text-dark-700 mb-1">
                      Concentration
                    </label>
                    <select
                      id="concentration"
                      name="concentration"
                      value={profile.concentration}
                      onChange={handleChange}
                      required
                      className="mt-1 block w-full bg-gray-50 dark:bg-dark-300 border border-gray-300 dark:border-dark-400 rounded-lg shadow-sm py-2.5 px-3 focus:outline-none focus:ring-accent-primary focus:border-accent-primary dark:focus:ring-accent-primary dark:focus:border-accent-primary sm:text-sm transition-all duration-150 dark:text-dark-700"
                    >
                      <option value="">Select a concentration</option>
                      {concentrations.map((conc) => (
                        <option key={conc} value={conc}>{conc}</option>
                      ))}
                    </select>
                  </div>
                  
                  {/* Year with enhanced styling */}
                  <div className="sm:col-span-3">
                    <label htmlFor="year" className="block text-sm font-medium text-gray-700 dark:text-dark-700 mb-1">
                      Year
                    </label>
                    <select
                      id="year"
                      name="year"
                      value={profile.year}
                      onChange={handleChange}
                      required
                      className="mt-1 block w-full bg-gray-50 dark:bg-dark-300 border border-gray-300 dark:border-dark-400 rounded-lg shadow-sm py-2.5 px-3 focus:outline-none focus:ring-accent-primary focus:border-accent-primary dark:focus:ring-accent-primary dark:focus:border-accent-primary sm:text-sm transition-all duration-150 dark:text-dark-700"
                    >
                      <option value="">Select your year</option>
                      {yearOptions.map((year) => (
                        <option key={year} value={year}>{year}</option>
                      ))}
                    </select>
                  </div>
                  
                  {/* Courses Taken with enhanced styling */}
                  <div className="sm:col-span-6">
                    <div className="flex justify-between items-center mb-1">
                      <label htmlFor="courses" className="block text-sm font-medium text-gray-700 dark:text-dark-700">
                        Courses You've Taken
                      </label>
                      <button
                        type="button"
                        onClick={() => setPasteModalOpen(true)}
                        className="text-sm text-accent-primary dark:text-accent-secondary hover:text-accent-tertiary dark:hover:text-accent-primary font-medium flex items-center"
                      >
                        <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4 mr-1" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 13h6m-3-3v6m5 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                        </svg>
                        Import Courses
                      </button>
                    </div>
                    
                    {/* Course input with direct event handling */}
                    <div className="mt-1 flex rounded-md shadow-sm">
                      <div className="flex w-full">
                        <input
                          type="text"
                          name="course-input"
                          id="course-input"
                          value={courseInput}
                          onChange={(e) => setCourseInput(e.target.value)}
                          onKeyPress={(e) => {
                            if (e.key === 'Enter') {
                              e.preventDefault();
                              handleAddCourse();
                            }
                          }}
                          placeholder="e.g., MATH 55, CS 50"
                          className="flex-1 min-w-0 block w-full px-3 py-3 rounded-l-lg border border-gray-300 dark:border-dark-400 bg-gray-50 dark:bg-dark-300 focus:outline-none focus:ring-accent-primary focus:border-accent-primary dark:focus:ring-accent-primary dark:focus:border-accent-primary dark:text-dark-700 dark:placeholder-dark-500 sm:text-sm transition-all duration-150"
                        />
                        <button
                          type="button"
                          onClick={handleAddCourse}
                          className="inline-flex items-center px-4 py-3 border border-transparent rounded-r-lg shadow-sm text-sm font-medium text-white bg-accent-primary hover:bg-accent-tertiary focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-accent-primary transition-colors"
                        >
                          Add
                        </button>
                      </div>
                    </div>
                    
                    {/* Courses List with enhanced styling */}
                    {profile.courses_taken.length > 0 && (
                      <div className="mt-3 p-3 bg-gray-50 dark:bg-dark-300 rounded-lg border border-gray-200 dark:border-dark-400">
                        <div className="text-xs font-medium text-gray-500 dark:text-dark-600 mb-2">Your Courses:</div>
                        <div className="flex flex-wrap gap-2">
                          {profile.courses_taken.map((course, index) => (
                            <span key={index} className="inline-flex rounded-full items-center py-1 pl-3 pr-1.5 text-sm font-medium bg-white dark:bg-dark-200 border border-gray-200 dark:border-dark-400 text-gray-800 dark:text-dark-700 shadow-sm">
                              {course}
                              <button
                                type="button"
                                onClick={() => handleRemoveCourse(index)}
                                className="flex-shrink-0 ml-1 h-4 w-4 rounded-full inline-flex items-center justify-center text-gray-400 dark:text-dark-500 hover:bg-gray-200 dark:hover:bg-dark-400 hover:text-gray-500 dark:hover:text-dark-700 focus:outline-none focus:bg-gray-500 focus:text-white transition-colors"
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
                    <label className="block text-sm font-medium text-gray-700 dark:text-dark-700 mb-1">
                      Academic Interests
                    </label>
                    <div className="mt-1 bg-gray-50 dark:bg-dark-300 p-3 rounded-lg border border-gray-200 dark:border-dark-400">
                      <div className="flex flex-wrap gap-2">
                        {interestOptions.map((interest) => (
                          <button
                            key={interest}
                            type="button"
                            onClick={() => toggleInterest(interest)}
                            className={`inline-flex items-center px-3 py-1.5 rounded-full text-sm font-medium transition-all duration-150
                              ${selectedInterests.includes(interest) 
                                ? 'bg-accent-primary text-white shadow-sm' 
                                : 'bg-white dark:bg-dark-200 border border-gray-200 dark:border-dark-400 text-gray-700 dark:text-dark-700 hover:bg-gray-100 dark:hover:bg-dark-300 shadow-sm'
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
                    <label className="block text-sm font-medium text-gray-700 dark:text-dark-700 mb-1">
                      Learning Preferences
                    </label>
                    <div className="mt-1 bg-gray-50 dark:bg-dark-300 p-3 rounded-lg border border-gray-200 dark:border-dark-400">
                      <div className="flex flex-wrap gap-2">
                        {learningOptions.map((preference) => (
                          <button
                            key={preference}
                            type="button"
                            onClick={() => togglePreference(preference)}
                            className={`inline-flex items-center px-3 py-1.5 rounded-full text-sm font-medium transition-all duration-150
                              ${selectedPreferences.includes(preference) 
                                ? 'bg-accent-primary text-white shadow-sm' 
                                : 'bg-white dark:bg-dark-200 border border-gray-200 dark:border-dark-400 text-gray-700 dark:text-dark-700 hover:bg-gray-100 dark:hover:bg-dark-300 shadow-sm'
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
                    className="inline-flex items-center px-5 py-2.5 border border-transparent rounded-lg shadow-sm text-sm font-medium text-white bg-accent-primary hover:bg-accent-tertiary focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-accent-primary dark:focus:ring-accent-secondary transition-all duration-200"
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
            <div className="bg-gray-50 dark:bg-dark-300 px-4 py-4 sm:px-8 border-t border-gray-200 dark:border-dark-400">
              <div className="flex items-center">
                <div className="flex-shrink-0">
                  <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 text-accent-primary" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                </div>
                <div className="ml-3">
                  <p className="text-sm text-gray-600 dark:text-dark-600">
                    The more details you provide, the better ChatHarvard can personalize course recommendations and academic advice.
                  </p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
      
      {/* Course Import Modal */}
      {pasteModalOpen && (
        <div className="fixed inset-0 z-50 overflow-y-auto">
          <div className="flex items-center justify-center min-h-screen pt-4 px-4 pb-20 text-center sm:block sm:p-0">
            <div className="fixed inset-0 transition-opacity" aria-hidden="true">
              <div className="absolute inset-0 bg-gray-500 dark:bg-dark-50 dark:bg-opacity-75 opacity-75"></div>
            </div>
            
            <span className="hidden sm:inline-block sm:align-middle sm:h-screen" aria-hidden="true">&#8203;</span>
            
            <div className="inline-block align-bottom bg-white dark:bg-dark-200 rounded-lg text-left overflow-hidden shadow-xl dark:shadow-card-dark transform transition-all sm:my-8 sm:align-middle sm:max-w-lg sm:w-full">
              <div className="px-4 pt-5 pb-4 sm:p-6 sm:pb-4">
                <div className="sm:flex sm:items-start">
                  <div className="mt-3 text-center sm:mt-0 sm:ml-4 sm:text-left w-full">
                    <h3 className="text-lg leading-6 font-medium text-gray-900 dark:text-dark-800">
                      Import Courses
                    </h3>
                    
                    {/* Tabs */}
                    <div className="mt-4 border-b border-gray-200 dark:border-dark-400">
                      <div className="flex -mb-px">
                        <button
                          onClick={() => setModalTab('paste')}
                          className={`py-2 px-4 text-sm font-medium mr-4 transition-colors
                            ${modalTab === 'paste' 
                              ? 'border-b-2 border-accent-primary text-accent-primary dark:text-accent-secondary' 
                              : 'text-gray-500 dark:text-dark-600 hover:text-gray-700 dark:hover:text-dark-700 hover:border-gray-300 dark:hover:border-dark-500'
                            }`}
                        >
                          Paste Course List
                        </button>
                        <button
                          onClick={() => setModalTab('upload')}
                          className={`py-2 px-4 text-sm font-medium transition-colors
                            ${modalTab === 'upload' 
                              ? 'border-b-2 border-accent-primary text-accent-primary dark:text-accent-secondary' 
                              : 'text-gray-500 dark:text-dark-600 hover:text-gray-700 dark:hover:text-dark-700 hover:border-gray-300 dark:hover:border-dark-500'
                            }`}
                        >
                          Upload Transcript PDF
                        </button>
                      </div>
                    </div>
                    
                    <div className="mt-4">
                      {modalTab === 'paste' ? (
                        <div>
                          <label htmlFor="course-paste" className="block text-sm font-medium text-gray-700 dark:text-dark-700 mb-1">
                            Paste your course list from website, email, or document
                          </label>
                          <textarea
                            id="course-paste"
                            rows={5}
                            className="shadow-sm mt-1 block w-full sm:text-sm border border-gray-300 dark:border-dark-400 rounded-md p-2 bg-white dark:bg-dark-300 text-gray-900 dark:text-dark-700 focus:ring-accent-primary focus:border-accent-primary dark:focus:ring-accent-primary dark:focus:border-accent-primary"
                            value={coursePasteText}
                            onChange={(e) => setCoursePasteText(e.target.value)}
                            placeholder="Paste text containing course codes like CS 50, MATH 21A, etc."
                          />
                          <p className="mt-2 text-sm text-gray-500 dark:text-dark-600">
                            We'll automatically extract course codes from the text.
                          </p>
                        </div>
                      ) : (
                        <div>
                          <FileUpload
                            accept=".pdf"
                            onUpload={handlePdfUpload}
                            disabled={uploadLoading}
                            label="Upload Transcript PDF"
                            helperText="We'll extract your course codes from the PDF"
                          />
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              </div>
              <div className="bg-gray-50 dark:bg-dark-300 px-4 py-3 sm:px-6 sm:flex sm:flex-row-reverse">
                {modalTab === 'paste' ? (
                  <button
                    type="button"
                    className="w-full inline-flex justify-center rounded-md border border-transparent shadow-sm px-4 py-2 bg-accent-primary text-base font-medium text-white hover:bg-accent-tertiary focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-accent-primary dark:focus:ring-accent-secondary sm:ml-3 sm:w-auto sm:text-sm"
                    onClick={handlePasteExtract}
                  >
                    Extract Courses
                  </button>
                ) : (
                  uploadLoading && (
                    <div className="w-full sm:w-auto sm:ml-3 flex justify-center">
                      <div className="inline-flex items-center px-4 py-2 text-base font-medium text-white">
                        <svg className="animate-spin -ml-1 mr-2 h-4 w-4 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                          <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                          <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                        </svg>
                        Processing...
                      </div>
                    </div>
                  )
                )}
                <button
                  type="button"
                  className="mt-3 w-full inline-flex justify-center rounded-md border border-gray-300 dark:border-dark-400 shadow-sm px-4 py-2 bg-white dark:bg-dark-200 text-base font-medium text-gray-700 dark:text-dark-700 hover:bg-gray-50 dark:hover:bg-dark-300 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-accent-primary dark:focus:ring-offset-dark-200 dark:focus:ring-accent-secondary sm:mt-0 sm:ml-3 sm:w-auto sm:text-sm"
                  onClick={() => setPasteModalOpen(false)}
                >
                  Cancel
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </>
  );
}

export default Profile;