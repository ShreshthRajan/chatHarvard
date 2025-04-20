import React, { useState, useRef } from 'react';

function FileUpload({ 
  accept = '.pdf',
  maxSize = 5, // Max size in MB
  onUpload,
  disabled = false,
  label = 'Upload File',
  helperText = 'Drag and drop a file here or click to browse'
}) {
  const [isDragging, setIsDragging] = useState(false);
  const [file, setFile] = useState(null);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const fileInputRef = useRef(null);

  const handleDragEnter = (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (!disabled) setIsDragging(true);
  };

  const handleDragLeave = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);
  };

  const handleDragOver = (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (!disabled) setIsDragging(true);
  };

  const validateFile = (file) => {
    // Check file type
    const fileType = file.type;
    const validTypes = accept.split(',').map(type => type.trim());
    const isPDF = fileType === 'application/pdf';
    
    if (!validTypes.includes(`.${file.name.split('.').pop()}`) && 
        !validTypes.includes(fileType) && 
        !isPDF && 
        !validTypes.includes('*')) {
      return {
        valid: false,
        error: `File type not supported. Please upload a file with extension: ${accept}`
      };
    }

    // Check file size
    const fileSize = file.size / 1024 / 1024; // Convert to MB
    if (fileSize > maxSize) {
      return {
        valid: false,
        error: `File size exceeds ${maxSize} MB limit`
      };
    }

    return { valid: true };
  };

  const handleFileChange = async (e) => {
    const selectedFile = e.target.files[0];
    handleFile(selectedFile);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);
    
    if (disabled) return;
    
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      const droppedFile = e.dataTransfer.files[0];
      handleFile(droppedFile);
    }
  };

  const handleFile = async (selectedFile) => {
    if (!selectedFile) return;
    
    // Reset states
    setError('');
    
    // Validate file
    const validation = validateFile(selectedFile);
    if (!validation.valid) {
      setError(validation.error);
      return;
    }
    
    setFile(selectedFile);
    
    // Process file if callback provided
    if (onUpload) {
      setLoading(true);
      try {
        await onUpload(selectedFile);
      } catch (err) {
        setError(`Error processing file: ${err.message}`);
      } finally {
        setLoading(false);
      }
    }
  };

  const handleClick = () => {
    if (!disabled && fileInputRef.current) {
      fileInputRef.current.click();
    }
  };

  const handleRemoveFile = (e) => {
    e.stopPropagation();
    setFile(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  return (
    <div className="w-full">
      <label className="block text-sm font-medium text-gray-700 mb-1">
        {label}
      </label>
      <div
        className={`mt-1 flex justify-center px-6 pt-5 pb-6 border-2 border-dashed rounded-lg cursor-pointer transition-colors ${
          isDragging ? 'border-harvard-crimson bg-harvard-light bg-opacity-20' :
          disabled ? 'border-gray-200 bg-gray-50 cursor-not-allowed' :
          'border-gray-300 hover:border-harvard-crimson'
        }`}
        onDragEnter={handleDragEnter}
        onDragLeave={handleDragLeave}
        onDragOver={handleDragOver}
        onDrop={handleDrop}
        onClick={handleClick}
      >
        <div className="space-y-1 text-center">
          {!file ? (
            <>
              <svg
                className={`mx-auto h-12 w-12 ${disabled ? 'text-gray-300' : 'text-gray-400'}`}
                stroke="currentColor"
                fill="none"
                viewBox="0 0 48 48"
                aria-hidden="true"
              >
                <path
                  d="M28 8H12a4 4 0 00-4 4v20m32-12v8m0 0v8a4 4 0 01-4 4H12a4 4 0 01-4-4v-4m32-4l-3.172-3.172a4 4 0 00-5.656 0L28 28M8 32l9.172-9.172a4 4 0 015.656 0L28 28m0 0l4 4m4-24h8m-4-4v8m-12 4h.02"
                  strokeWidth={2}
                  strokeLinecap="round"
                  strokeLinejoin="round"
                />
              </svg>
              <div className="flex text-sm text-gray-600">
                <label
                  htmlFor="file-upload"
                  className={`relative font-medium ${
                    disabled ? 'text-gray-400' : 'text-harvard-crimson hover:text-harvard-dark'
                  }`}
                >
                  {disabled ? 'Upload disabled' : 'Upload a file'}
                </label>
                <p className="pl-1 text-gray-500">{disabled ? '' : 'or drag and drop'}</p>
              </div>
              <p className="text-xs text-gray-500">{helperText}</p>
              <p className="text-xs text-gray-500">Maximum file size: {maxSize}MB</p>
            </>
          ) : (
            <div className="flex items-center justify-center space-x-2">
              <div className="flex items-center bg-gray-100 py-2 px-3 rounded-lg text-sm text-gray-900">
                <svg className="h-5 w-5 text-gray-500 mr-2" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 21h10a2 2 0 002-2V9.414a1 1 0 00-.293-.707l-5.414-5.414A1 1 0 0012.586 3H7a2 2 0 00-2 2v14a2 2 0 002 2z" />
                </svg>
                <span className="truncate max-w-xs">{file.name}</span>
                <span className="text-xs text-gray-500 ml-2">
                  ({(file.size / 1024 / 1024).toFixed(2)} MB)
                </span>
                {!loading && (
                  <button
                    type="button"
                    onClick={handleRemoveFile}
                    className="ml-2 text-gray-500 hover:text-gray-700 focus:outline-none"
                  >
                    <svg className="h-4 w-4" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                    </svg>
                  </button>
                )}
              </div>
              {loading && (
                <div className="loader" />
              )}
            </div>
          )}
        </div>
        <input
          id="file-upload"
          ref={fileInputRef}
          name="file-upload"
          type="file"
          className="sr-only"
          accept={accept}
          onChange={handleFileChange}
          disabled={disabled}
        />
      </div>
      {error && (
        <p className="mt-2 text-sm text-red-600">{error}</p>
      )}
    </div>
  );
}

export default FileUpload;