import React, { createContext, useContext, useState, useEffect } from 'react';
import axios from '../api/axios';

export const AuthContext = createContext(null);

export const AuthProvider = ({ children }) => {
    const [user, setUser] = useState(null);
    const [isAuthenticated, setIsAuthenticated] = useState(false);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        // Check for stored token and user data
        const token = localStorage.getItem('token');
        const userData = localStorage.getItem('user');
        
        console.log('AuthContext: Checking authentication on mount');
        console.log('AuthContext: Token exists:', !!token);
        console.log('AuthContext: User data exists:', !!userData);
        
        if (token && userData) {
            try {
                const parsedUserData = JSON.parse(userData);
                console.log('AuthContext: Loaded user from localStorage:', parsedUserData);
                setUser(parsedUserData);
                setIsAuthenticated(true);
                console.log('AuthContext: Authentication state set to true');
            } catch (error) {
                console.error('AuthContext: Error parsing user data:', error);
                localStorage.removeItem('user');
                localStorage.removeItem('token');
                console.log('AuthContext: Cleared invalid localStorage data');
            }
        } else {
            console.log('AuthContext: No token or user data found, staying unauthenticated');
        }
        setLoading(false);
        console.log('AuthContext: Loading state set to false');
    }, []);

    const login = async (credentials) => {
        try {
            const response = await axios.post('/api/login', credentials);
            // Debug: Log the user object received from backend
            console.log('Login response user data:', response.data.user);
            // Debug: Log the full response
            console.log('Full login response:', response.data);
            // Save token and user data to localStorage
            localStorage.setItem('token', response.data.token);
            localStorage.setItem('user', JSON.stringify(response.data.user));
            // Debug: Log what is being stored in localStorage
            console.log('User object stored in localStorage:', JSON.parse(localStorage.getItem('user')));
            setUser(response.data.user);
            setIsAuthenticated(true);
            return response.data;
        } catch (error) {
            console.error('Login error:', error);
            throw error;
        }
    };

    const logout = () => {
        localStorage.removeItem('token');
        localStorage.removeItem('user');
        setUser(null);
        setIsAuthenticated(false);
    };

    if (loading) {
        return (
            <AuthContext.Provider value={{ 
                user: null, 
                isAuthenticated: false,
                login: () => Promise.reject('Loading...'), 
                logout: () => {} 
            }}>
                {children}
            </AuthContext.Provider>
        );
    }

    return (
        <AuthContext.Provider value={{ 
            user, 
            isAuthenticated,
            login, 
            logout 
        }}>
            {children}
        </AuthContext.Provider>
    );
};

export const useAuth = () => useContext(AuthContext); 