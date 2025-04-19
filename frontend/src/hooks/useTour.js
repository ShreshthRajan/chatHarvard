// src/hooks/useTour.js - Tour hook
import { useState, useEffect } from 'react';

export function useTour(steps, autoStart = false) {
  const [currentStep, setCurrentStep] = useState(0);
  const [isTourActive, setIsTourActive] = useState(autoStart);
  const [hasSeenTour, setHasSeenTour] = useState(false);

  useEffect(() => {
    const tourSeen = localStorage.getItem('tourSeen') === 'true';
    setHasSeenTour(tourSeen);
    
    if (autoStart && !tourSeen) {
      setIsTourActive(true);
    }
  }, [autoStart]);

  const startTour = () => {
    setCurrentStep(0);
    setIsTourActive(true);
  };

  const endTour = () => {
    setIsTourActive(false);
    localStorage.setItem('tourSeen', 'true');
    setHasSeenTour(true);
  };

  const nextStep = () => {
    if (currentStep < steps.length - 1) {
      setCurrentStep(prev => prev + 1);
    } else {
      endTour();
    }
  };

  const prevStep = () => {
    if (currentStep > 0) {
      setCurrentStep(prev => prev - 1);
    }
  };

  const resetTourHistory = () => {
    localStorage.removeItem('tourSeen');
    setHasSeenTour(false);
  };

  return {
    currentStep,
    isTourActive,
    hasSeenTour,
    currentStepData: isTourActive ? steps[currentStep] : null,
    startTour,
    endTour,
    nextStep,
    prevStep,
    resetTourHistory
  };
}