// src/components/components/coursecard.jsx - New component for course display
import React from 'react';

export function CourseCard({ 
  courseCode, 
  title, 
  instructor, 
  qScore = null, 
  workload = null, 
  description,
  onClick 
}) {
  // Calculate background color based on Q score
  const getQScoreColor = (score) => {
    if (!score) return 'bg-gray-100';
    if (score >= 4.5) return 'bg-green-100 text-green-800';
    if (score >= 4.0) return 'bg-green-50 text-green-700';
    if (score >= 3.5) return 'bg-yellow-50 text-yellow-800';
    if (score >= 3.0) return 'bg-yellow-100 text-yellow-800';
    return 'bg-red-50 text-red-700';
  };

  const getWorkloadLabel = (hours) => {
    if (!hours) return 'Unknown';
    if (hours < 5) return 'Light';
    if (hours < 10) return 'Moderate';
    if (hours < 15) return 'Substantial';
    return 'Heavy';
  };

  return (
    <div 
      className="bg-white border border-gray-200 rounded-xl shadow-sm hover:shadow-md transition-shadow duration-200 overflow-hidden cursor-pointer"
      onClick={onClick}
    >
      <div className="p-5">
        <div className="flex justify-between items-start">
          <div>
            <h3 className="text-lg font-medium text-gray-900">{courseCode}</h3>
            <p className="text-sm text-gray-500">{instructor}</p>
          </div>
          <div className="flex space-x-2">
            {qScore && (
              <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getQScoreColor(qScore)}`}>
                Q: {qScore.toFixed(1)}
              </span>
            )}
            {workload && (
              <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-gray-100 text-gray-800">
                {getWorkloadLabel(workload)}
              </span>
            )}
          </div>
        </div>
        <h4 className="mt-2 text-base font-medium text-gray-800">{title}</h4>
        <p className="mt-2 text-sm text-gray-600 line-clamp-3">{description}</p>
      </div>
      <div className="px-5 py-3 bg-gray-50 border-t border-gray-200">
        <div className="text-xs font-medium text-harvard-crimson hover:text-harvard-dark transition-colors duration-150">
          View details →
        </div>
      </div>
    </div>
  );
}