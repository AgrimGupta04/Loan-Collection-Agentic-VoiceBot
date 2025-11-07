import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';

// A reusable SVG icon component for the hamburger menu and close icon
const MenuIcon = ({ isOpen }) => (
    <svg
        className="w-6 h-6 text-white"
        fill="none"
        stroke="currentColor"
        viewBox="0 0 24 24"
        xmlns="http://www.w3.org/2000/svg"
    >
        {isOpen ? (
            <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M6 18L18 6M6 6l12 12"
            />
        ) : (
            <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M4 6h16M4 12h16m-7 6h7"
            />
        )}
    </svg>
);

// A reusable navigation link component that wraps react-router-dom's Link
const NavLink = ({ to, children, isActive, onClick }) => (
    <Link
        to={to}
        onClick={onClick}
        className={`px-3 py-2 rounded-md text-sm font-medium transition-all duration-300 ease-in-out focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-offset-slate-900 focus:ring-white ${
            isActive
                ? 'bg-white/10 text-white'
                : 'text-blue-100 hover:bg-white/10 hover:text-white'
        } transform hover:scale-105`}
    >
        {children}
    </Link>
);

function Header() {
    // State to manage the mobile menu visibility
    const [isMenuOpen, setIsMenuOpen] = useState(false);
    const navigate = useNavigate();

    const handleNavClick = () => {
        window.scrollTo({
            top: 0,
            behavior: 'smooth'
        });
        setIsMenuOpen(false); // Close mobile menu on navigation
    };
    
    // Updated navItems to be an array of objects
    const navItems = [
        { name: 'Home', link: '/' },
        { name: 'All Customers', link: '/all-customers' },
        { name: 'Add Customer', link: '/add-customer' },
        { name: 'Pending', link: '/pending' },
        { name: 'Upload', link: '/upload' },
        { name: 'Received', link: '/received' },
    ];

    return (
        <header className='bg-gradient-to-r from-blue-900 via-slate-900 to-black shadow-lg text-white sticky top-0 z-50'>
            <div className='max-w-7xl mx-auto px-4 sm:px-6 lg:px-8'>
                <div className='flex items-center justify-between h-16'>

                    {/* Left Section: Title */}
                    <div className='flex flex-row'>
                        <div className='flex items-center scale-125 pr-3'>
                        <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="white" class="bi bi-wallet2" viewBox="0 0 16 16">
                        <path d="M12.136.326A1.5 1.5 0 0 1 14 1.78V3h.5A1.5 1.5 0 0 1 16 4.5v9a1.5 1.5 0 0 1-1.5 1.5h-13A1.5 1.5 0 0 1 0 13.5v-9a1.5 1.5 0 0 1 1.432-1.499zM5.562 3H13V1.78a.5.5 0 0 0-.621-.484zM1.5 4a.5.5 0 0 0-.5.5v9a.5.5 0 0 0 .5.5h13a.5.5 0 0 0 .5-.5v-9a.5.5 0 0 0-.5-.5z"/>
                        </svg>
                        </div>
                         <h1 onClick={() => { navigate('/'); handleNavClick('Home'); }} className='font-extrabold text-xl md:text-2xl font-serif tracking-wider transition-transform duration-300 hover:scale-105 cursor-pointer'>
                            Loan Collector
                        </h1>
                    </div>

                    {/* Center Section: Desktop Navigation */}
                    <div className='hidden md:block'>
                        <div className='ml-10 flex items-baseline space-x-4 '>
                            {navItems.map((item) => (
                                <NavLink
                                    key={item.name}
                                    to={item.link}
                                    onClick={() => handleNavClick(item.name)}
                                >
                                    {item.name}
                                </NavLink>
                            ))}
                        </div>
                    </div>

                    {/* Right Section: GitHub Icon */}
                    <div className='hidden md:block'>
                         <a href="https://github.com/AgrimGupta04" target="_blank" rel="noopener noreferrer" className="p-2 rounded-full">
                            <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6 text-white" fill="currentColor" viewBox="0 0 24 24">
                                <path d="M12 2C6.477 2 2 6.484 2 12.017c0 4.425 2.865 8.18 6.839 9.504.5.092.682-.217.682-.483 0-.237-.008-.868-.013-1.703-2.782.605-3.369-1.343-3.369-1.343-.454-1.158-1.11-1.466-1.11-1.466-.908-.62.069-.608.069-.608 1.003.07 1.531 1.032 1.531 1.032.892 1.53 2.341 1.088 2.91.832.092-.647.35-1.088.636-1.338-2.22-.253-4.555-1.113-4.555-4.951 0-1.093.39-1.988 1.029-2.688-.103-.253-.446-1.272.098-2.65 0 0 .84-.27 2.75 1.026A9.564 9.564 0 0112 6.844c.85.004 1.705.115 2.504.337 1.909-1.296 2.747-1.027 2.747-1.027.546 1.379.202 2.398.1 2.651.64.7 1.028 1.595 1.028 2.688 0 3.848-2.339 4.695-4.566 4.943.359.31.678.923.678 1.861 0 1.343-.012 2.426-.012 2.756 0 .268.18.58.688.482A10.019 10.019 0 0022 12c0-5.523-4.477-10-10-10z" />
                            </svg>
                        </a>
                    </div>
                    
                    {/* Mobile Menu Button */}
                    <div className='-mr-2 flex md:hidden'>
                        <button
                            onClick={() => setIsMenuOpen(!isMenuOpen)}
                            type="button"
                            className="inline-flex items-center justify-center p-2 rounded-md text-blue-100 hover:text-white hover:bg-white/10 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-offset-slate-900 focus:ring-white"
                            aria-controls="mobile-menu"
                            aria-expanded={isMenuOpen}
                        >
                            <span className="sr-only">Open main menu</span>
                            <MenuIcon isOpen={isMenuOpen} />
                        </button>
                    </div>

                </div>
            </div>

            {/* Mobile Menu Panel */}
            <div
                className={`md:hidden absolute w-full transition-all duration-300 ease-in-out overflow-hidden ${isMenuOpen ? 'max-h-96' : 'max-h-0'}`}
                id="mobile-menu"
            >
                <div className="flex flex-col px-2 pt-2 pb-3 space-y-1 sm:px-3 bg-slate-900/95 backdrop-blur-sm">
                     {navItems.map((item) => (
                        <NavLink
                            key={item.name}
                            to={item.link}
                            onClick={() => handleNavClick(item.name)}
                        >
                            {item.name}
                        </NavLink>
                    ))}
                    <div className="pt-4 pb-2 border-t border-blue-700">
                        <a href="https://github.com/AgrimGupta04" target="_blank" rel="noopener noreferrer" className="flex items-center space-x-3 px-3 py-2 text-base font-medium text-blue-100 rounded-md hover:bg-white/10 hover:text-white">
                            <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6" fill="currentColor" viewBox="0 0 24 24">
                                <path d="M12 2C6.477 2 2 6.484 2 12.017c0 4.425 2.865 8.18 6.839 9.504.5.092.682-.217.682-.483 0-.237-.008-.868-.013-1.703-2.782.605-3.369-1.343-3.369-1.343-.454-1.158-1.11-1.466-1.11-1.466-.908-.62.069-.608.069-.608 1.003.07 1.531 1.032 1.531 1.032.892 1.53 2.341 1.088 2.91.832.092-.647.35-1.088.636-1.338-2.22-.253-4.555-1.113-4.555-4.951 0-1.093.39-1.988 1.029-2.688-.103-.253-.446-1.272.098-2.65 0 0 .84-.27 2.75 1.026A9.564 9.564 0 0112 6.844c.85.004 1.705.115 2.504.337 1.909-1.296 2.747-1.027 2.747-1.027.546 1.379.202 2.398.1 2.651.64.7 1.028 1.595 1.028 2.688 0 3.848-2.339 4.695-4.566 4.943.359.31.678.923.678 1.861 0 1.343-.012 2.426-.012 2.756 0 .268.18.58.688.482A10.019 10.019 0 0022 12c0-5.523-4.477-10-10-10z" />
                            </svg>
                            <span>GitHub</span>
                        </a>
                    </div>
                </div>
            </div>
        </header>
    );
}

export default Header;
                           