import React, { useState } from 'react';

const FileUpload = () => {
  const [file, setFile] = useState(null);

  const handleFileChange = (e) => {
    setFile(e.target.files[0]);
  };

  const uploadFile = () => {
    if (file) {
      console.log('Uploading file:', file);
      // Add logic to upload file to backend
    }
  };

  return (
    <div className="file-upload">
      <input type="file" onChange={handleFileChange} />
      <button onClick={uploadFile}>Upload</button>
    </div>
  );
};

export default FileUpload;
