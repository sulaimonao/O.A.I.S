import React, { useEffect, useState } from 'react';
import io from 'socket.io-client';

const socket = io('http://localhost:5000'); // Backend server URL

const Chat = () => {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');

  useEffect(() => {
    socket.on('message', (message) => {
      setMessages((prevMessages) => [...prevMessages, message]);
    });
  }, []);

  const sendMessage = () => {
    socket.emit('message', input);
    setInput('');
  };

  return (
    <div className="chat">
      <div className="messages">
        {messages.map((msg, index) => (
          <div key={index} className="message">{msg}</div>
        ))}
      </div>
      <input
        value={input}
        onChange={(e) => setInput(e.target.value)}
        placeholder="Type a message..."
      />
      <button onClick={sendMessage}>Send</button>
    </div>
  );
};

export default Chat;
