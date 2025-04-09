const development = {
    API_URL: 'http://localhost:5000'
};

const production = {
    API_URL: import.meta.env.VITE_API_URL || 'https://api.example.com' // This will be replaced with your actual production URL
};

const config = import.meta.env.MODE === 'production' ? production : development;

export default config; 