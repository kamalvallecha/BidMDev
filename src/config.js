
const development = {
    API_URL: ''  // Empty string for relative URLs
};

const production = {
    API_URL: ''  // Empty string for relative URLs
};

const config = import.meta.env.MODE === 'production' ? production : development;

export default config;
