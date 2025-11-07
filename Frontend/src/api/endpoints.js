// Backend URL from environment variable
const url = import.meta.env.VITE_APP_BACKEND_URL;

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
export const addCustomer = async (customerData) => {
    const response = await fetch(`${url}/add-customer`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(customerData),
    });

    if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to add customer');
    }

    return await response.json();
};

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
