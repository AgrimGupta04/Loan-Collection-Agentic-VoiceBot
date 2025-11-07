import react from 'react';
import HomePage from './pages/HomePage';
import Header from './components/common/header.jsx';
import Footer from './components/common/footer.jsx';
import AllCustomers from './pages/AllCustomers.jsx';
import AddCustomerForm from './components/core/addCustomer.jsx';
import PendingCustomers from './pages/PendingCustomers.jsx';
import ReceivedCustomers from './pages/UpdatedCustomers.jsx';
import UploadRecording from './pages/UploadRecording.jsx';
import { Routes, Route, Navigate} from 'react-router-dom';
import ScrollToTop from './components/scrollToTop.jsx';
import './App.css'

function App() {

  return (
    <div className='flex flex-col min-h-screen bg-gray-700'>
      <Header />
      <Routes>
        <Route path="/" element={<HomePage />} />
        <Route path="/all-customers" element={<AllCustomers />} />
        <Route path="/pending" element={<PendingCustomers />} />
        <Route path="/received" element={<ReceivedCustomers />} />
        <Route path="/upload" element={<UploadRecording />} />
        <Route path="/add-customer" element={<AddCustomerForm />} />
        <Route path="*" element={<Navigate to="/" />} />
      </Routes>
      <ScrollToTop />
      <Footer />
    </div>
  )
}
export default App;

