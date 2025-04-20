import React, { useState } from 'react';

function CourseCard({ course }) {
  const [expanded, setExpanded] = useState(false);

  // Default course structure if not provided
  const {
    code = '',
    title = '',
    description = '',
    instructor = '',
    term = '',
    rating = null,
    workload = null,
    prerequisites = [],
    enrollment = null,
    tags = []
  } = course || {};

  // Format rating with color coding
  const getRatingColor = (rating) => {
    if (!rating) return 'text-gray-400';
    if (rating >= 4.5) return 'text-green-600';
    if (rating >= 4.0) return 'text-green-500';
    if (rating >= 3.5) return 'text-yellow-600';
    if (rating >= 3.0) return 'text-yellow-500';
    return 'text-red-500';
  };

  // Format workload with color coding
  const getWorkloadColor = (hours) => {
    if (!hours) return 'text-gray-400';
    if (hours <= 5) return 'text-green-600';
    if (hours <= 8) return 'text-green-500';
    if (hours <= 12) return 'text-yellow-600';
    if (hours <= 15) return 'text-yellow-500';
    return 'text-red-500';
  };

  return (
    <div className="card overflow-hidden transition-all duration-200 hover:shadow-hover">
      <div className="px-4 py-4 sm:px-6">
        <div className="flex justify-between">
          <div>
            <h3 className="text-lg leading-6 font-medium text-gray-900 flex items-center">
              {code} 
              {term && (
                <span className="ml-2 badge badge-primary">{term}</span>
              )}
            </h3>
            <p className="text-base mt-1 font-medium">{title}</p>
            {instructor && (
              <p className="text-sm text-gray-500 mt-1">Instructor: {instructor}</p>
            )}
          </div>
          <div className="flex flex-col items-end">
            {rating !== null && (
              <div className="flex items-center">
                <span className={`text-lg font-bold ${getRatingColor(rating)}`}>
                  {rating.toFixed(1)}
                </span>
                <span className="text-xs text-gray-500 ml-1">/5.0</span>
                <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 text-yellow-400 ml-1" viewBox="0 0 20 20" fill="currentColor">
                  <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
                </svg>
              </div>
            )}
            {workload !== null && (
              <div className="flex items-center mt-1">
                <span className={`text-sm font-medium ${getWorkloadColor(workload)}`}>
                  {workload} hrs/week
                </span>
                <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4 text-gray-400 ml-1" viewBox="0 0 20 20" fill="currentColor">
                  <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm1-12a1 1 0 10-2 0v4a1 1 0 00.293.707l2.828 2.829a1 1 0 101.415-1.415L11 9.586V6z" clipRule="evenodd" />
                </svg>
              </div>
            )}
            {enrollment !== null && (
              <div className="text-xs text-gray-500 mt-1">
                Enrollment: {enrollment} students
              </div>
            )}
          </div>
        </div>
        
        {tags.length > 0 && (
          <div className="flex flex-wrap gap-1 mt-2">
            {tags.map((tag, index) => (
              <span 
                key={index} 
                className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-gray-100 text-gray-800"
              >
                {tag}
              </span>
            ))}
          </div>
        )}
        
        {prerequisites.length > 0 && (
          <div className="mt-2">
            <span className="text-xs font-medium text-gray-500">Prerequisites: </span>
            <span className="text-xs text-gray-700">
              {prerequisites.join(', ')}
            </span>
          </div>
        )}
        
        <div className="mt-2">
          <p className={`text-sm text-gray-600 ${expanded ? '' : 'line-clamp-2'}`}>
            {description}
          </p>
          {description && description.length > 150 && (
            <button
              className="text-xs font-medium text-harvard-crimson hover:text-harvard-dark mt-1"
              onClick={() => setExpanded(!expanded)}
            >
              {expanded ? 'Show less' : 'Show more'}
            </button>
          )}
        </div>
      </div>
    </div>
  );
}

export default CourseCard;