import React from 'react';

const Hero = () => {
  return (
    <div id="home" className="relative overflow-hidden bg-slate-900 min-h-screen flex items-center justify-center">
      {/* Background decoration */}
      <div className="absolute inset-0">
        <div className="absolute inset-0 bg-gradient-to-br from-blue-900 via-slate-900 to-black opacity-80"></div>
        <div 
          className="absolute inset-0 mix-blend-overlay" 
          style={{
            backgroundImage: `url("data:image/svg+xml,%3Csvg width='60' height='60' viewBox='0 0 60 60' xmlns='http://www.w3.org/2000/svg'%3E%3Cg fill='none' fill-rule='evenodd'%3E%3Cg fill='%23ffffff' fill-opacity='0.04'%3E%3Cpath d='M36 34v-4h-2v4h-4v2h4v4h2v-4h4v-2h-4zm0-30V0h-2v4h-4v2h4v4h2V6h4V4h-4zM6 34v-4H4v4H0v2h4v4h2v-4h4v-2H6zM6 4V0H4v4H0v2h4v4h2V6h4V4H6z'/%3E%3C/g%3E%3C/g%3E%3C/svg%3E")`
          }}
        ></div>
      </div>

      <div className="relative max-w-7xl mx-auto py-24 px-4 sm:py-32 lg:py-40 sm:px-6 lg:px-8 text-center">
        <h1 className="text-4xl font-extrabold tracking-tight text-white sm:text-5xl md:text-6xl">
          <span className="block hover:scale-105 transition-transform duration-300">Streamline Your</span>
          <span className="block text-blue-400 animate-pulse hover:scale-105 transition-transform duration-300">Loan Collections</span>
        </h1>
        <p className="mt-6 max-w-lg mx-auto text-lg text-blue-200 sm:max-w-3xl">
          Efficiently manage customer accounts, track payments, and get a clear overview of your portfolio. All in one powerful, easy-to-use dashboard.
        </p>
        <div className="mt-10 max-w-sm mx-auto sm:max-w-none sm:flex sm:justify-center">
          <div className="space-y-4 sm:space-y-0 sm:mx-auto">
            <a
              href="/pending"
              className="w-full sm:w-auto flex items-center justify-center px-8 py-3 border border-transparent text-base font-medium rounded-full text-white bg-blue-600 hover:bg-blue-700 md:py-4 md:text-lg md:px-10 transition-transform transform hover:scale-105 shadow-lg"
            >
              Getting Started
            </a>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Hero;

