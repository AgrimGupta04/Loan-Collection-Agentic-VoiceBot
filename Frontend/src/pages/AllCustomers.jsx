import React, { useState, useEffect } from 'react';
import MakeCallButton from '../components/core/makeCall';
import {fetchAllCustomers} from '../api/endpoints';

// Mock customer data - replace with API call
// const mockCustomers = [
//     { id: 1, name: 'John Doe', email: 'john.doe@example.com', loanAmount: 5000, status: 'Pending'},
//     { id: 2, name: 'Jane Smith', email: 'jane.smith@example.com', loanAmount: 12000, status: 'Received'},
//     { id: 3, name: 'Sam Wilson', email: 'sam.wilson@example.com', loanAmount: 7500, status: 'Pending'},
//     { id: 4, name: 'Alice Johnson', email: 'alice.j@example.com', loanAmount: 25000, status: 'Received'},
//     { id: 5, name: 'Mike Brown', email: 'mike.brown@example.com', loanAmount: 3200, status: 'Pending'},
//     { id: 6, name: 'Emily Davis', email: 'emily.d@example.com', loanAmount: 1500, status: 'Received'},
// ];


function AllCustomers() {

    const [customers, setCustomers] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    useEffect(() => {
        const fetchCustomers = async () => {
            try {
                const data = await fetchAllCustomers('all-customers');
                setCustomers(data.customers || []);
            } catch (e) {
                setError(e.message);
            } finally {
                setLoading(false);
            }
        };

        fetchCustomers();
    }, [setCustomers]);


    if (loading) {
        return (
            <div className="flex justify-center items-center h-screen bg-slate-50">
                <div className="text-xl font-semibold text-gray-700">Loading Customers...</div>
            </div>
        );
    }

    if (error) {
        return (
            <div className="flex justify-center items-center h-screen bg-red-50">
                <div className="text-xl font-semibold text-red-700">Error: {error}</div>
            </div>
        );
    }

    return (
        <div className="bg-gradient-to-br from-blue-900 to-slate-900  min-h-screen p-4 sm:p-6 lg:p-8">
            <div className="max-w-7xl mx-auto">
                <h1 className="text-4xl font-bold text-white mb-6">All Customers</h1>
                <div className="bg-white shadow-xl rounded-lg overflow-hidden">
                    <div className="overflow-x-auto">
                        <table className="min-w-full divide-y divide-gray-200">
                            <thead className="bg-gray-100">
                                <tr>
                                    <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Name</th>
                                    <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Phone</th>
                                    <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Loan Amount</th>
                                    <th scope='col' className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Due Date</th>
                                    <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Status</th>
                                    <th scope='col' className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Make Call</th>
                                </tr>
                            </thead>
                            <tbody className="bg-white divide-y divide-gray-200">
                                {
                                    customers.map((customer) => (
                                        <tr key={customer.id}>
                                            <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">{customer.name}</td>
                                            <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{customer.phone}</td>
                                            <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">${customer.loan_amount}</td>
                                            <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{customer.due_date}</td>
                                            <td className="px-6 py-4 whitespace-nowrap text-sm">
                                                <span className={`px-3 py-1 text-xs font-semibold rounded-full ${customer.call_status === 'Pending' ? 'bg-yellow-200 text-yellow-800' : 'bg-green-200 text-green-800'}`}>
                                                    {customer.call_status}
                                                </span>
                                            </td>
                                            <td className="px-6 py-4 whitespace-nowrap text-sm">
                                                {customer.call_status === 'Pending' && (
                                                    <MakeCallButton customerId={customer.id} customerName={customer.name} />
                                                )}
                                            </td>
                                        </tr>
                                    ))
                                }
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>
            
        </div>
    );
}

export default AllCustomers;
