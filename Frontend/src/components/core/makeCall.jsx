import React, { useState } from 'react';
import {startCall} from '../../api/endpoints';

// A reusable SVG icon for the call button
const CallIcon = () => (
    <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
        <path strokeLinecap="round" strokeLinejoin="round" d="M3 5a2 2 0 012-2h3.28a1 1 0 01.948.684l1.498 4.493a1 1 0 01-.502 1.21l-2.257 1.13a11.042 11.042 0 005.516 5.516l1.13-2.257a1 1 0 011.21-.502l4.493 1.498a1 1 0 01.684.949V19a2 2 0 01-2 2h-1C9.716 21 3 14.284 3 6V5z" />
    </svg>
);

function MakeCallButton({ customerId, customerName }) {
    const [isCalling, setIsCalling] = useState(false);

    const handleCall = async () => {
        setIsCalling(true);

        try {
            await startCall(customerId);
            alert(`Call initiated to ${customerName}`);
        } catch (error) {
            console.error("Call failed:", error);
        } finally {
            setIsCalling(false);
        }
    };

    return (
        <button
            onClick={handleCall}
            disabled={isCalling}
            className={`flex items-center justify-center px-4 py-2 text-sm font-medium rounded-md transition-colors duration-200 focus:outline-none focus:ring-2 focus:ring-offset-2 ${
                isCalling
                    ? 'bg-gray-400 text-gray-800 cursor-not-allowed'
                    : 'bg-blue-600 text-white hover:bg-blue-700 focus:ring-blue-500'
            }`}
        >
            {isCalling ? (
                <>
                    {/* Loading spinner */}
                    <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-white" xmlns="http://www.w.org/2000/svg" fill="none" viewBox="0 0 24 24">
                        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                    </svg>
                    Calling...
                </>
            ) : (
                <>
                    <CallIcon />
                    Call
                </>
            )}
        </button>
    );
}

export default MakeCallButton;
