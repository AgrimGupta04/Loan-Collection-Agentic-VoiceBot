import React from 'react';

// Reusable Feature Card component
const FeatureCard = ({ icon, title, children }) => (
    <div className="p-8 rounded-3xl shadow-lg bg-gray-50 hover:shadow-xl hover:-translate-y-1 transition-all duration-300">
        <div className="flex items-center justify-center h-12 w-12 hover:scale-105 transition-transform duration-300 rounded-4xl bg-gradient-to-tr from-blue-900 to-blue-700 text-white">
            {icon}
        </div>
        <h3 className="mt-6 text-xl font-semibold text-gray-900 hover:text-blue-900 hover:translate-x-1 hover:underline-offset-1 transition-all duration-300">{title}</h3>
        <p className="mt-4 text-base text-gray-600 hover:scale-105 hover:text-gray-900 transition-all duration-300">
            {children}
        </p>
    </div>
);

function About() {
  return (
    <section id="about" className="py-20 bg-gradient-to-b from-white to-slate-300 scroll-mt-16">
        {/* scroll-mt-16 adds a top margin to the scroll target to offset the sticky header */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center">
          <h2 className="font-bold text-blue-800 tracking-wide uppercase text-4xl hover:scale-115 hover:text-gray-900 transition-transform duration-300">Our Mission</h2>
          <p className="mt-2 text-3xl font-extrabold text-gray-900 sm:text-4xl hover:scale-110 hover:text-blue-800 transition-transform duration-300">
            A Better Way to Manage Collections
          </p>
          <p className="mt-4 max-w-2xl mx-auto text-xl text-gray-500 hover:scale-105 hover:text-gray-900 transition-transform duration-300">
            Our Loan Collector dashboard is designed to simplify loan management, providing agents with the tools they need to track, manage, and collect payments efficiently.
          </p>
        </div>
        
        <div className="mt-12 grid gap-10 md:grid-cols-2 lg:grid-cols-3">
            <FeatureCard 
                title="Efficient Tracking" 
                icon={<svg className="h-6 w-6" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>}
            >
                Easily monitor all your customer accounts, payment statuses (pending or received), and loan histories in one centralized dashboard.
            </FeatureCard>

            <FeatureCard 
                title="Streamlined Payments"
                icon={<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" class="bi bi-currency-rupee" viewBox="0 0 16 16">
                        <path d="M4 3.06h2.726c1.22 0 2.12.575 2.325 1.724H4v1.051h5.051C8.855 7.001 8 7.558 6.788 7.558H4v1.317L8.437 14h2.11L6.095 8.884h.855c2.316-.018 3.465-1.476 3.688-3.049H12V4.784h-1.345c-.08-.778-.357-1.335-.793-1.732H12V2H4z"/>
                    </svg>}
            >
                Our platform provides a clear overview of collected payments, reducing manual errors and saving you valuable time.
            </FeatureCard>

             <FeatureCard 
                title="Accessible Anywhere"
                icon={<svg className="h-6 w-6" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 18h.01M7 21h10a2 2 0 002-2V5a2 2 0 00-2-2H7a2 2 0 00-2 2v14a2 2 0 002 2z" /></svg>}
            >
                 With a fully responsive design, you can manage your loan collections on your desktop, tablet, or smartphone.
            </FeatureCard>
        </div>
      </div>
    </section>
  );
}

export default About;
