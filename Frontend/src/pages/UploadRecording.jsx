import React, { useState, useEffect } from 'react';
import { uploadRecording, fetchPendingCustomers } from '../api/endpoints';

// Reusable Notification component for feedback
function Notification({ message, type, onDismiss }) {
    const [visible, setVisible] = useState(false);

    useEffect(() => {
        if (message) {
            setVisible(true);
            const timer = setTimeout(() => {
                handleDismiss();
            }, 5000);
            return () => clearTimeout(timer);
        }
    }, [message, type]);

    const handleDismiss = () => {
        setVisible(false);
        setTimeout(() => onDismiss(), 300);
    };

    if (!message) return null;

    const baseClasses = "fixed top-5 right-5 w-full max-w-sm p-4 rounded-lg shadow-lg text-white transition-all duration-300 ease-in-out transform z-50 backdrop-blur-sm";
    const typeClasses = {
        success: 'bg-green-500/80',
        error: 'bg-red-500/80',
        info: 'bg-blue-500/80'
    };
    const visibilityClasses = visible ? 'opacity-100 translate-y-0' : 'opacity-0 -translate-y-5';

    return (
        <div className={`${baseClasses} ${typeClasses[type] || 'bg-gray-700/80'} ${visibilityClasses}`}>
            <div className="flex items-start">
                <div className="flex-1 text-sm font-medium">{message}</div>
                <button onClick={handleDismiss} className="ml-4 p-1 rounded-full hover:bg-white/20 focus:outline-none">
                    <svg className="h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12" />
                    </svg>
                </button>
            </div>
        </div>
    );
}

function UploadRecording() {
    const [customers, setCustomers] = useState([]);
    const [selectedCustomer, setSelectedCustomer] = useState('');
    const [selectedFile, setSelectedFile] = useState(null);
    const [isUploading, setIsUploading] = useState(false);
    const [notification, setNotification] = useState({ message: '', type: '' });

    useEffect(() => {
        const fetchCustomers = async () => {
            try {
                const data = await fetchPendingCustomers('pending-customers');
                setCustomers(data.customers || []);
            } catch (error) {
                console.error("Error fetching customers:", error);
            }
        };

        fetchCustomers();
    }, []);

    const handleFileChange = (event) => {
        if (event.target.files && event.target.files[0]) {
            setSelectedFile(event.target.files[0]);
        }
    };

    const handleSubmit = async (event) => {
        event.preventDefault();
        if (!selectedCustomer || !selectedFile) {
            alert('Please select a customer and a file to upload.');
            return;
        }

        setIsUploading(true);
        const customerName = customers.find(c => c.id == selectedCustomer)?.name || 'Selected Customer';

        const formData = new FormData();
        formData.append('file', selectedFile, selectedFile.name); // Correct key is 'file'

        try {
            // --- Replaced simulation with actual API call ---
            const result = await uploadRecording(selectedCustomer, formData);
            
            showNotification(result.message || 'Recording successfully uploaded!', 'success');
            setSelectedCustomer('');
            setSelectedFile(null);
            event.target.reset(); // Resets the file input

        } catch (error) {
            console.error('Upload failed:', error);
            // Display the error message from the API call
            showNotification(error.message || 'Upload failed. Please try again.', 'error');
        } finally {
            setIsUploading(false);
        }
    };

    const showNotification = (message, type) => setNotification({ message, type });
    const dismissNotification = () => setNotification({ message: '', type: '' });

    return (
        <>
            <Notification message={notification.message} type={notification.type} onDismiss={dismissNotification} />
            <div className="bg-gradient-to-br from-blue-900 to-slate-900 min-h-screen flex items-center justify-center p-4">
                <div className="max-w-md w-full bg-slate-800/50 backdrop-blur-sm border border-slate-700 shadow-2xl rounded-xl p-8 transform transition-all hover:scale-[1.01] duration-300">
                    <h1 className="text-3xl font-bold text-white mb-6 text-center">Upload Voice Recording</h1>
                    <form onSubmit={handleSubmit} className="space-y-6">
                        <div>
                            <label htmlFor="customer" className="block text-sm font-medium text-gray-300">Choose a Person</label>
                            <select
                                id="customer"
                                value={selectedCustomer}
                                onChange={(e) => setSelectedCustomer(e.target.value)}
                                className="mt-1 block w-full pl-3 pr-10 py-2 text-base bg-slate-700 border-slate-600 text-white focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm rounded-md"
                                required
                            >
                                <option value="" disabled>Select a customer</option>
                                {customers.map(customer => (
                                    <option key={customer.id} value={customer.id}>{customer.name}</option>
                                ))}
                            </select>
                        </div>
                        <div>
                            <label htmlFor="file-upload" className="block text-sm font-medium text-gray-300">Select Voice File</label>
                            <div className="mt-1 flex justify-center px-6 pt-5 pb-6 border-2 border-slate-600 border-dashed rounded-md">
                                <div className="space-y-1 text-center">
                                    <svg className="mx-auto h-12 w-12 text-gray-500" stroke="currentColor" fill="none" viewBox="0 0 48 48" aria-hidden="true"><path d="M28 8H12a4 4 0 00-4 4v20m32-12v8m0 0v8a4 4 0 01-4 4H12a4 4 0 01-4-4v-4m32-4l-3.172-3.172a4 4 0 00-5.656 0L28 28M8 32l9.172-9.172a4 4 0 015.656 0L28 28m0 0l4 4m4-24h8m-4-4v8" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" /></svg>
                                    <div className="flex text-sm text-gray-400">
                                        <label htmlFor="file-upload" className="relative cursor-pointer bg-slate-800/10 rounded-md font-medium text-blue-400 hover:text-blue-300 focus-within:outline-none focus-within:ring-2 focus-within:ring-offset-2 focus-within:ring-offset-slate-800 focus-within:ring-blue-500">
                                            <span>Upload a file</span>
                                            <input id="file-upload" name="file-upload" type="file" className="sr-only" onChange={handleFileChange} accept="audio/*" required />
                                        </label>
                                        <p className="pl-1">or drag and drop</p>
                                    </div>
                                    <p className="text-xs text-gray-500">WAV</p>
                                    {selectedFile && <p className="text-sm text-green-400 mt-2">File selected: {selectedFile.name}</p>}
                                </div>
                            </div>
                        </div>
                        <div>
                            <button type="submit" disabled={isUploading} className="w-full flex justify-center py-3 px-4 border border-transparent rounded-md shadow-lg text-sm font-medium text-white bg-blue-600 hover:bg-blue-500 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-offset-slate-800 focus:ring-blue-500 disabled:bg-slate-600 disabled:cursor-not-allowed transition-all duration-300 hover:shadow-blue-500/50"
                            >
                                {isUploading ? (
                                    <>
                                        <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24"><circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle><path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path></svg>
                                        Uploading...
                                    </>
                                ) : 'Update'}
                            </button>
                        </div>
                    </form>
                </div>
            </div>
        </>
    );
}

export default UploadRecording;

