
// src/services/apiService.js

const API_BASE_URL = 'http://localhost:5000/api';

export const fetchData = async () => {
    try {
        const response = await fetch(`${API_BASE_URL}/data`);
        if (!response.ok) {
            throw new Error(`HTTP error! Status: ${response.status}`);
        }
        return await response.json();
    } catch (error) {
        console.error('Error fetching data:', error);
        throw error;
    }
};
