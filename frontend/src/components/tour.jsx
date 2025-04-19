// src/components/components/tour.jsx - New component
import React, { useState, useEffect } from 'react';
import { Transition } from '@headlessui/react';

export function TourStep({ 
  target, 
  title, 
  content, 
  position = 'bottom', 
  isOpen, 
  onClose, 
  onNext, 
  onPrev, 
  stepNumber, 
  totalSteps 
}) {
  const [coords, setCoords] = useState({ top: 0, left: 0 });

  useEffect(() => {
    if (isOpen && target) {
      const updatePosition = () => {
        const element = document.querySelector(target);
        if (!element) return;

        const rect = element.getBoundingClientRect();
        const newCoords = { top: 0, left: 0 };

        switch (position) {
          case 'top':
            newCoords.top = rect.top - 12 - 100; // height of tooltip + offset
            newCoords.left = rect.left + rect.width / 2 - 150; // half width of tooltip
            break;
          case 'bottom':
            newCoords.top = rect.bottom + 12;
            newCoords.left = rect.left + rect.width / 2 - 150;
            break;
          case 'left':
            newCoords.top = rect.top + rect.height / 2 - 50;
            newCoords.left = rect.left - 12 - 300;
            break;
          case 'right':
            newCoords.top = rect.top + rect.height / 2 - 50;
            newCoords.left = rect.right + 12;
            break;
          default:
            newCoords.top = rect.bottom + 12;
            newCoords.left = rect.left + rect.width / 2 - 150;
        }

        setCoords(newCoords);
      };

      updatePosition();
      window.addEventListener('resize', updatePosition);
      window.addEventListener('scroll', updatePosition);

      return () => {
        window.removeEventListener('resize', updatePosition);
        window.removeEventListener('scroll', updatePosition);
      };
    }
  }, [isOpen, target, position]);

  if (!isOpen) return null;

  return (
    <Transition
      show={isOpen}
      enter="transition-opacity duration-300"
      enterFrom="opacity-0"
      enterTo="opacity-100"
      leave="transition-opacity duration-200"
      leaveFrom="opacity-100"
      leaveTo="opacity-0"
    >
      <div 
        className="fixed z-50 w-300 p-4 bg-white rounded-lg shadow-lg border border-gray-200"
        style={{ 
          top: `${coords.top}px`, 
          left: `${coords.left}px`,
          maxWidth: '300px'
        }}
      >
        <div className="font-medium text-lg text-gray-900 mb-2">{title}</div>
        <p className="text-gray-600 text-sm mb-4">{content}</p>
        <div className="flex items-center justify-between">
          <div className="text-xs text-gray-500">
            Step {stepNumber} of {totalSteps}
          </div>
          <div className="flex space-x-2">
            {stepNumber > 1 && (
              <button
                onClick={onPrev}
                className="text-sm px-3 py-1 border border-gray-300 rounded-md text-gray-700 hover:bg-gray-50"
              >
                Back
              </button>
            )}
            {stepNumber < totalSteps ? (
              <button
                onClick={onNext}
                className="text-sm px-3 py-1 bg-harvard-crimson text-white rounded-md hover:bg-harvard-dark"
              >
                Next
              </button>
            ) : (
              <button
                onClick={onClose}
                className="text-sm px-3 py-1 bg-harvard-crimson text-white rounded-md hover:bg-harvard-dark"
              >
                Finish
              </button>
            )}
          </div>
        </div>
      </div>
    </Transition>
  );
}