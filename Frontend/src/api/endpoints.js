// Backend URL from environment variable - Make sure this is just the base string
const url = import.meta.env.VITE_APP_BACKEND_URL;

// Helper function for consistent error handling
async function handleResponse(response) {
    if (!response.ok) {
        // Log the status and try to read the response body as text for debugging
        console.error(`HTTP error! status: ${response.status}`);
        try {
            const errorText = await response.text();
            console.error("Error response body:", errorText);
        } catch (textError) {
            console.error("Could not read error response body:", textError);
        }
        throw new Error(`HTTP error! status: ${response.status}`);
    }
    // Only parse JSON if the response was successful (status 2xx)
    return await response.json();
}

// All Customer form endpoint "all-customers"
export const fetchAllCustomers = async (endpoint) => {
    try {
        const response = await fetch(`${url}/${endpoint}`);
        return await handleResponse(response); // Use helper
    } catch (error) {
        console.error(`Error fetching ${endpoint}:`, error);
        throw error;
    }
};

export const fetchPendingCustomers = async (endpoint) => {
    try {
        const response = await fetch(`${url}/${endpoint}`);
        return await handleResponse(response); // Use helper
    } catch (error) {
        console.error(`Error fetching ${endpoint}:`, error);
        throw error;
    }
};

// Assuming you have an endpoint for this, otherwise remove
export const fetchUpdatedCustomers = async (endpoint) => {
    try {
        const response = await fetch(`${url}/${endpoint}`);
        return await handleResponse(response); // Use helper
    } catch (error) {
        console.error(`Error fetching ${endpoint}:`, error);
        throw error;
    }
};

export const uploadRecording = async (customerId, formData) => {
    try {
        const response = await fetch(`${url}/upload-recording/${customerId}`, {
            method: 'POST',
            body: formData, // No Content-Type needed, browser sets it for FormData
        });
        return await handleResponse(response); // Use helper
    } catch (error) {
        console.error("Error uploading recording:", error);
        throw error;
    }
};

export const startCall = async (customerId) => {
    try {
        const response = await fetch(`${url}/start-call/${customerId}`, {
            method: 'POST',
        });
        return await handleResponse(response); // Use helper
    } catch (error) {
        console.error("Error starting call:", error);
        throw error;
    }
};