import React, { useState } from 'react';
import { ChevronDownIcon, ChevronUpIcon, ClockIcon, UserGroupIcon, AcademicCapIcon, StarIcon } from '@heroicons/react/24/outline';

function CourseCard({ course, onClick, className = '' }) {
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
    if (!rating) return 'text-gray-400 dark:text-dark-500';
    if (rating >= 4.5) return 'course-rating-high';
    if (rating >= 4.0) return 'course-rating-high';
    if (rating >= 3.5) return 'course-rating-medium';
    if (rating >= 3.0) return 'course-rating-medium';
    return 'course-rating-low';
  };

  // Format workload with color coding
  const getWorkloadColor = (hours) => {
    if (!hours) return 'text-gray-400 dark:text-dark-500';
    if (hours <= 5) return 'workload-low';
    if (hours <= 8) return 'workload-low';
    if (hours <= 12) return 'workload-medium';
    if (hours <= 15) return 'workload-medium';
    return 'workload-high';
  };

  return (
    <div 
      className={`course-card ${className} ${onClick ? 'cursor-pointer' : ''}`}
      onClick={onClick}
    >
      <div className="px-4 py-4 sm:px-6">
        <div className="flex justify-between">
          <div>
            <h3 className="text-lg leading-6 font-medium text-gray-900 dark:text-dark-800 flex items-center">
              {code} 
              {term && (
                <span className="ml-2 badge badge-primary">{term}</span>
              )}
            </h3>
            <p className="text-base mt-1 font-medium dark:text-dark-700">{title}</p>
            {instructor && (
              <div className="flex items-center text-sm text-gray-500 dark:text-dark-600 mt-1">
                <AcademicCapIcon className="h-4 w-4 mr-1.5" />
                {instructor}
              </div>
            )}
          </div>
          <div className="flex flex-col items-end">
            {rating !== null && (
              <div className="flex items-center">
                <span className={`text-lg font-bold ${getRatingColor(rating)}`}>
                  {rating.toFixed(1)}
                </span>
                <span className="text-xs text-gray-500 dark:text-dark-600 ml-1">/5.0</span>
                <StarIcon className="h-5 w-5 text-yellow-400 dark:text-yellow-500 ml-1" />
              </div>
            )}
            {workload !== null && (
              <div className="flex items-center mt-1">
                <ClockIcon className="h-4 w-4 mr-1 text-gray-400 dark:text-dark-500" />
                <span className={`text-sm font-medium ${getWorkloadColor(workload)}`}>
                  {workload} hrs/week
                </span>
              </div>
            )}
            {enrollment !== null && (
              <div className="flex items-center text-xs text-gray-500 dark:text-dark-600 mt-1">
                <UserGroupIcon className="h-3.5 w-3.5 mr-1 text-gray-400 dark:text-dark-500" />
                {enrollment} students
              </div>
            )}
          </div>
        </div>
        
        {tags.length > 0 && (
          <div className="flex flex-wrap gap-1 mt-2">
            {tags.map((tag, index) => (
              <span 
                key={index} 
                className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-gray-100 text-gray-800 dark:bg-dark-300 dark:text-dark-700"
              >
                {tag}
              </span>
            ))}
          </div>
        )}
        
        {prerequisites.length > 0 && (
          <div className="mt-2">
            <span className="text-xs font-medium text-gray-500 dark:text-dark-600">Prerequisites: </span>
            <span className="text-xs text-gray-700 dark:text-dark-700">
              {prerequisites.join(', ')}
            </span>
          </div>
        )}
        
        {description && (
          <div className="mt-2">
            <p className={`text-sm text-gray-600 dark:text-dark-600 ${expanded ? '' : 'line-clamp-2'}`}>
              {description}
            </p>
            {description.length > 150 && (
              <button
                className="text-xs font-medium text-harvard-crimson dark:text-accent-primary hover:text-harvard-dark dark:hover:text-accent-secondary mt-1 flex items-center"
                onClick={(e) => {
                  e.stopPropagation();
                  setExpanded(!expanded);
                }}
              >
                {expanded ? (
                  <>
                    Show less
                    <ChevronUpIcon className="h-3.5 w-3.5 ml-0.5" />
                  </>
                ) : (
                  <>
                    Show more
                    <ChevronDownIcon className="h-3.5 w-3.5 ml-0.5" />
                  </>
                )}
              </button>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

export default CourseCard;