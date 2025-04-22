import React from 'react';
import { Dialog, Transition } from '@headlessui/react';
import { XMarkIcon, StarIcon, ClockIcon } from '@heroicons/react/24/outline';

export function CourseComparisonModal({ isOpen, onClose, courses = [] }) {
  if (!courses || courses.length === 0) return null;
  
  // Helper functions for color coding
  const getRatingColorClass = (rating) => {
    if (!rating) return 'bg-gray-300 dark:bg-dark-400';
    if (rating >= 4.5) return 'bg-green-500 dark:bg-green-500';
    if (rating >= 4.0) return 'bg-green-400 dark:bg-green-400';
    if (rating >= 3.5) return 'bg-yellow-400 dark:bg-yellow-400';
    if (rating >= 3.0) return 'bg-yellow-500 dark:bg-yellow-500';
    return 'bg-red-500 dark:bg-red-500';
  };
  
  const getWorkloadColorClass = (workload) => {
    if (!workload) return 'bg-gray-300 dark:bg-dark-400';
    if (workload <= 5) return 'bg-green-500 dark:bg-green-500';
    if (workload <= 10) return 'bg-green-400 dark:bg-green-400';
    if (workload <= 15) return 'bg-yellow-400 dark:bg-yellow-400';
    return 'bg-red-500 dark:bg-red-500';
  };
  
  return (
    <Transition appear show={isOpen} as={React.Fragment}>
      <Dialog as="div" className="relative z-50" onClose={onClose}>
        <Transition.Child
          as={React.Fragment}
          enter="ease-out duration-300"
          enterFrom="opacity-0"
          enterTo="opacity-100"
          leave="ease-in duration-200"
          leaveFrom="opacity-100"
          leaveTo="opacity-0"
        >
          <div className="fixed inset-0 bg-black bg-opacity-25 dark:bg-opacity-50" />
        </Transition.Child>

        <div className="fixed inset-0 overflow-y-auto">
          <div className="flex min-h-full items-center justify-center p-4 text-center">
            <Transition.Child
              as={React.Fragment}
              enter="ease-out duration-300"
              enterFrom="opacity-0 scale-95"
              enterTo="opacity-100 scale-100"
              leave="ease-in duration-200"
              leaveFrom="opacity-100 scale-100"
              leaveTo="opacity-0 scale-95"
            >
              <Dialog.Panel className="w-full max-w-4xl transform overflow-hidden rounded-xl bg-white dark:bg-dark-200 text-left align-middle shadow-xl dark:shadow-card-dark transition-all">
                <div className="flex justify-between items-center p-6 border-b border-gray-200 dark:border-dark-400">
                  <Dialog.Title as="h3" className="text-lg font-medium text-gray-900 dark:text-dark-800">
                    Course Comparison
                  </Dialog.Title>
                  <button
                    type="button"
                    className="text-gray-400 dark:text-dark-500 hover:text-gray-500 dark:hover:text-dark-600 focus:outline-none"
                    onClick={onClose}
                  >
                    <span className="sr-only">Close</span>
                    <XMarkIcon className="h-6 w-6" />
                  </button>
                </div>
                <div className="p-6">
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    {courses.map((course, index) => (
                      <div key={index} className="bg-gray-50 dark:bg-dark-300 p-4 rounded-lg border border-gray-200 dark:border-dark-400">
                        <h4 className="text-lg font-medium text-gray-900 dark:text-dark-800">{course.courseCode || course.code}</h4>
                        <h5 className="text-base font-medium text-gray-800 dark:text-dark-700 mt-1">{course.title}</h5>
                        
                        <div className="mt-4 space-y-3">
                          <div>
                            <span className="text-sm font-medium text-gray-700 dark:text-dark-700">Instructor:</span>
                            <span className="text-sm text-gray-600 dark:text-dark-600 ml-2">{course.instructor}</span>
                          </div>
                          
                          <div className="flex items-center">
                            <span className="text-sm font-medium text-gray-700 dark:text-dark-700 flex items-center">
                              <StarIcon className="h-4 w-4 mr-1 text-gray-500 dark:text-dark-600" />
                              Q Score:
                            </span>
                            <div className="ml-2 bg-white dark:bg-dark-200 px-2 py-1 rounded border border-gray-200 dark:border-dark-400">
                              <div className="flex items-center">
                                <div className="w-24 h-2 bg-gray-200 dark:bg-dark-400 rounded-full overflow-hidden">
                                  <div 
                                    className={`h-full rounded-full ${getRatingColorClass(course.qScore || course.rating)}`}
                                    style={{ width: `${Math.min(100, ((course.qScore || course.rating) / 5) * 100)}%` }}
                                  ></div>
                                </div>
                                <span className="ml-2 text-sm font-medium text-gray-700 dark:text-dark-700">
                                  {(course.qScore || course.rating)?.toFixed(1) || 'N/A'}
                                </span>
                              </div>
                            </div>
                          </div>
                          
                          <div className="flex items-center">
                            <span className="text-sm font-medium text-gray-700 dark:text-dark-700 flex items-center">
                              <ClockIcon className="h-4 w-4 mr-1 text-gray-500 dark:text-dark-600" />
                              Workload:
                            </span>
                            <div className="ml-2 bg-white dark:bg-dark-200 px-2 py-1 rounded border border-gray-200 dark:border-dark-400">
                              <div className="flex items-center">
                                <div className="w-24 h-2 bg-gray-200 dark:bg-dark-400 rounded-full overflow-hidden">
                                  <div 
                                    className={`h-full rounded-full ${getWorkloadColorClass(course.workload)}`}
                                    style={{ width: `${Math.min(100, (course.workload / 20) * 100)}%` }}
                                  ></div>
                                </div>
                                <span className="ml-2 text-sm font-medium text-gray-700 dark:text-dark-700">
                                  {course.workload || 'N/A'} hrs/week
                                </span>
                              </div>
                            </div>
                          </div>
                          
                          <div>
                            <span className="text-sm font-medium text-gray-700 dark:text-dark-700">Description:</span>
                            <p className="text-sm text-gray-600 dark:text-dark-600 mt-1">{course.description}</p>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
                <div className="bg-gray-50 dark:bg-dark-300 p-4 border-t border-gray-200 dark:border-dark-400 flex justify-end">
                  <button
                    type="button"
                    className="inline-flex justify-center rounded-md border border-transparent bg-harvard-crimson dark:bg-accent-primary px-4 py-2 text-sm font-medium text-white hover:bg-harvard-dark dark:hover:bg-accent-tertiary focus:outline-none focus-visible:ring-2 focus-visible:ring-harvard-crimson dark:focus-visible:ring-accent-primary focus-visible:ring-offset-2 transition-colors"
                    onClick={onClose}
                  >
                    Close
                  </button>
                </div>
              </Dialog.Panel>
            </Transition.Child>
          </div>
        </div>
      </Dialog>
    </Transition>
  );
}