import React, { useState } from 'react';
import { addCustomer } from '../../api/endpoints'; // Import the new API function

function AddCustomerForm() {
    const [name, setName] = useState('');
    const [phone, setPhone] = useState('');
    const [loanAmount, setLoanAmount] = useState('');
    const [dueDate, setDueDate] = useState('');

    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);
    const [success, setSuccess] = useState(null);

    const handleSubmit = async (e) => {
        e.preventDefault();
        setLoading(true);
        setError(null);
        setSuccess(null);

        const customerData = {
            name: name,
            phone: phone,
            loan_amount: parseFloat(loanAmount), // Ensure it's a number
            due_date: dueDate,
            call_status: 'Pending' // Default status
        };

        try {
            await addCustomer(customerData);
            setSuccess('Customer added successfully!');

            // Clear the form
            setName('');
            setPhone('');
            setLoanAmount('');
            setDueDate('');

        } catch (e) {
            setError(e.message);
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="bg-gradient-to-br from-blue-900 to-slate-900  min-h-screen p-4 sm:p-6 lg:p-8">
            <div className="max-w-7xl mx-auto">
                <div className="bg-white shadow-xl rounded-lg overflow-hidden mb-6">
                    <h2 className="text-2xl font-semibold text-gray-900 p-6 border-b border-gray-200">
                        Add New Customer
                    </h2>
                    <form onSubmit={handleSubmit} className="p-6 space-y-4">
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                            <div>
                                <label htmlFor="name" className="block text-sm font-medium text-gray-700">Full Name</label>
                                <input
                                    type="text"
                                    id="name"
                                    value={name}
                                    onChange={(e) => setName(e.target.value)}
                                    className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
                                    required
                                />
                            </div>
                            <div>
                                <label htmlFor="phone" className="block text-sm font-medium text-gray-700">Phone Number</label>
                                <input
                                    type="tel"
                                    id="phone"
                                    value={phone}
                                    onChange={(e) => setPhone(e.target.value)}
                                    className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
                                    required
                                />
                            </div>
                            <div>
                                <label htmlFor="loanAmount" className="block text-sm font-medium text-gray-700">Loan Amount ($)</label>
                                <input
                                    type="number"
                                    id="loanAmount"
                                    value={loanAmount}
                                    onChange={(e) => setLoanAmount(e.target.value)}
                                    className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
                                    required
                                />
                            </div>
                            <div>
                                <label htmlFor="dueDate" className="block text-sm font-medium text-gray-700">Due Date</label>
                                <input
                                    type="date"
                                    id="dueDate"
                                    value={dueDate}
                                    onChange={(e) => setDueDate(e.target.value)}
                                    className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
                                    required
                                />
                            </div>
                        </div>

                        {/* Status Messages */}
                        {error && <div className="text-sm text-red-600">{error}</div>}
                        {success && <div className="text-sm text-green-600">{success}</div>}

                        <div className="flex justify-end">
                            <button
                                type="submit"
                                disabled={loading}
                                className="inline-flex justify-center py-2 px-4 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50"
                            >
                                {loading ? 'Adding...' : 'Add Customer'}
                            </button>
                        </div>
                    </form>
                </div>
            </div>

        </div>
    );
}

export default AddCustomerForm;