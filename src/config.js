
const config = {
    API_URL: window.location.hostname === 'localhost' 
        ? 'http://localhost:5000'
        : `${window.location.protocol}//${window.location.hostname}:5000`
};

export default config;
