import React from 'react';
import { Link } from 'react-router-dom';

const Header = () => (
  <header>
    <nav>
      <ul>
        <li><Link to="/">Dashboard</Link></li>
        <li><Link to="/chat">Chat</Link></li>
        <li><Link to="/code-execution">Code Execution</Link></li>
        <li><Link to="/file-upload">File Upload</Link></li>
        <li><Link to="/devices">Devices</Link></li>
        <li><Link to="/history">History</Link></li>
        <li><Link to="/profile">Profile</Link></li>
      </ul>
    </nav>
  </header>
);

export default Header;
