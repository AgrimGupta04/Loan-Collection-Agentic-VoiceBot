// Backend URL from environment variable
const BACKEND_URL = import.meta.env.VITE_APP_BACKEND_URL;
const url = BACKEND_URL;

// All Customer form endpoint "all-customers"
 export const fetchAllCustomers = async(endpoint) => {
    try {
        const response = await fetch(`${url}/${endpoint}`);
        const data = await response.json();
        return data;
    } catch (error) {
        console.error("Error fetching data:", error);
        throw error;
    }
}

export const fetchPendingCustomers = async(endpoint) => {
    try {
        const response = await fetch(`${url}/${endpoint}`);
        return response.json();
    } catch (error) {
        console.error("Error fetching data:", error);
        throw error;
    }
}

export const fetchUpdatedCustomers = async(endpoint) => {
    try {
        const response = await fetch(`${url}/${endpoint}`);
        return response.json();
    } catch (error) {
        console.error("Error fetching data:", error);
        throw error;
    }
}

export const uploadRecording = async(customerId, formData) => {
    try {
        const response = await fetch(`${url}/upload-recording/${customerId}`, {
            method: 'POST',
            body: formData,
        });
        return response.json();
    } catch (error) {
        console.error("Error uploading recording:", error);
        throw error;
    }
}

export const startCall = async(customerId) => {
    try {
        const response = await fetch(`${url}/start-call/${customerId}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ customerId }),
        });
        return response.json();
    } catch (error) {
        console.error("Error starting call:", error);
        throw error;
    }
}
