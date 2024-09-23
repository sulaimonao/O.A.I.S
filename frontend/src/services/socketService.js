// frontend/src/services/socketService.js

import { io } from 'socket.io-client';

const SOCKET_URL = 'http://localhost:5000'; // Update if different

export const socket = io(SOCKET_URL, {
    transports: ['websocket'],
    secure: false,
    reconnection: true,
    reconnectionAttempts: Infinity,
    reconnectionDelay: 1000,
    reconnectionDelayMax: 5000,
});

socket.on('connect', () => {
    console.log('Connected to Socket.IO server');
});

socket.on('disconnect', () => {
    console.log('Disconnected from Socket.IO server');
});

// Export the socket instance to use in components
export default socket;
