// src/components/components/coursecomparisonmodal.jsx - New component for course comparison
import React from 'react';
import { Dialog, Transition } from '@headlessui/react';
import { XMarkIcon } from '@heroicons/react/24/outline';

export function CourseComparisonModal({ isOpen, onClose, courses = [] }) {
  if (!courses || courses.length === 0) return null;
  
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
          <div className="fixed inset-0 bg-black bg-opacity-25" />
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
              <Dialog.Panel className="w-full max-w-4xl transform overflow-hidden rounded-xl bg-white text-left align-middle shadow-xl transition-all">
                <div className="flex justify-between items-center p-6 border-b border-gray-200">
                  <Dialog.Title as="h3" className="text-lg font-medium text-gray-900">
                    Course Comparison
                  </Dialog.Title>
                  <button
                    type="button"
                    className="text-gray-400 hover:text-gray-500"
                    onClick={onClose}
                  >
                    <span className="sr-only">Close</span>
                    <XMarkIcon className="h-6 w-6" />
                  </button>
                </div>
                <div className="p-6">
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    {courses.map((course, index) => (
                      <div key={index} className="bg-gray-50 p-4 rounded-lg border border-gray-200">
                        <h4 className="text-lg font-medium text-gray-900">{course.courseCode}</h4>
                        <h5 className="text-base font-medium text-gray-800 mt-1">{course.title}</h5>
                        
                        <div className="mt-4 space-y-3">
                          <div>
                            <span className="text-sm font-medium text-gray-700">Instructor:</span>
                            <span className="text-sm text-gray-600 ml-2">{course.instructor}</span>
                          </div>
                          
                          <div className="flex items-center">
                            <span className="text-sm font-medium text-gray-700">Q Score:</span>
                            <div className="ml-2 bg-white px-2 py-1 rounded border border-gray-200">
                              <div className="flex items-center">
                                <div className="w-24 h-2 bg-gray-200 rounded-full overflow-hidden">
                                  <div 
                                    className={`h-full rounded-full ${
                                      course.qScore >= 4.5 ? 'bg-green-500' :
                                      course.qScore >= 4.0 ? 'bg-green-400' :
                                      course.qScore >= 3.5 ? 'bg-yellow-400' :
                                      course.qScore >= 3.0 ? 'bg-yellow-500' :
                                      'bg-red-500'
                                    }`}
                                    style={{ width: `${Math.min(100, (course.qScore / 5) * 100)}%` }}
                                  ></div>
                                </div>
                                <span className="ml-2 text-sm font-medium">{course.qScore?.toFixed(1) || 'N/A'}</span>
                              </div>
                            </div>
                          </div>
                          
                          <div className="flex items-center">
                            <span className="text-sm font-medium text-gray-700">Workload:</span>
                            <div className="ml-2 bg-white px-2 py-1 rounded border border-gray-200">
                              <div className="flex items-center">
                                <div className="w-24 h-2 bg-gray-200 rounded-full overflow-hidden">
                                  <div 
                                    className={`h-full rounded-full ${
                                      course.workload <= 5 ? 'bg-green-500' :
                                      course.workload <= 10 ? 'bg-green-400' :
                                      course.workload <= 15 ? 'bg-yellow-400' :
                                      'bg-red-500'
                                    }`}
                                    style={{ width: `${Math.min(100, (course.workload / 20) * 100)}%` }}
                                  ></div>
                                </div>
                                <span className="ml-2 text-sm font-medium">{course.workload || 'N/A'} hrs/week</span>
                              </div>
                            </div>
                          </div>
                          
                          <div>
                            <span className="text-sm font-medium text-gray-700">Description:</span>
                            <p className="text-sm text-gray-600 mt-1">{course.description}</p>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
                <div className="bg-gray-50 p-4 border-t border-gray-200 flex justify-end">
                  <button
                    type="button"
                    className="inline-flex justify-center rounded-md border border-transparent bg-harvard-crimson px-4 py-2 text-sm font-medium text-white hover:bg-harvard-dark focus:outline-none focus-visible:ring-2 focus-visible:ring-harvard-crimson focus-visible:ring-offset-2"
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