import React from 'react';
import { BrowserRouter as Router, Route, Switch } from 'react-router-dom';
import Header from './Header';
import Sidebar from './Sidebar';
import Dashboard from './Dashboard';
import Chat from './Chat';
import CodeExecution from './CodeExecution';
import FileUpload from './FileUpload';
import Devices from './Devices';
import History from './History';
import Profile from './Profile';

const App = () => (
  <Router>
    <div className="app-container">
      <Header />
      <Sidebar />
      <div className="content">
        <Switch>
          <Route path="/" exact component={Dashboard} />
          <Route path="/chat" component={Chat} />
          <Route path="/code-execution" component={CodeExecution} />
          <Route path="/file-upload" component={FileUpload} />
          <Route path="/devices" component={Devices} />
          <Route path="/history" component={History} />
          <Route path="/profile" component={Profile} />
        </Switch>
      </div>
    </div>
  </Router>
);

export default App;
