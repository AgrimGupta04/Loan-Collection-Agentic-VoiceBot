import react from 'react';

function Footer() {
    const year = new Date().getFullYear();

    return (
        <>
            <footer className='bg-gradient-to-b  from-blue-900 to-slate-900 border-t-gray-300 border-t-1 font-serif text-white p-2 flex flex-col gap-4 items-center justify-center'>
                <div className='container mx-auto px-4 py-6 flex flex-col gap-10'>

                    <div className='grid grid-cols-1 md:grid-cols-3 gap-8'>
                        <div className='flex flex-col justify-items-center'>
                            <h2 className='text-xl  font-bold mb-1 tracking-wide'>Loan Collection Agent</h2>
                            <p className='text-sm font-extralight'>Your trusted partner in managing loan collections.</p>
                            <br />
                            <div className='flex flex-row justify-items-center'>
                                {/* github icon */}
                                <a href="https://github.com/AgrimGupta04">
                                    <svg xmlns="http://www.w3.org/2000/svg" className="h-8 w-8 hover:fill-white text-white hover:scale-115 transition-transform duration-300" fill="none" viewBox="0 0 24 24" stroke="currentcolor" strokeWidth={1}>
                                        <path d="M12 2C6.477 2 2 6.484 2 12.017c0 4.425 2.865 8.18 6.839 9.504.5.092.682-.217.682-.483 0-.237-.008-.868-.013-1.703-2.782.605-3.369-1.343-3.369-1.343-.454-1.158-1.11-1.466-1.11-1.466-.908-.62.069-.608.069-.608 1.003.07 1.531 1.032 1.531 1.032.892 1.53 2.341 1.088 2.91.832.092-.647.35-1.088.636-1.338-2.22-.253-4.555-1.113-4.555-4.951 0-1.093.39-1.988 1.029-2.688-.103-.253-.446-1.272.098-2.65 0 0 .84-.27 2.75 1.026A9.564 9.564 0 0112 6.844c.85.004 1.705.115 2.504.337 1.909-1.296 2.747-1.027 2.747-1.027.546 1.379.202 2.398.1 2.651.64.7 1.028 1.595 1.028 2.688 0 3.848-2.339 4.695-4.566 4.943.359.31.678.923.678 1.861 0 1.343-.012 2.426-.012 2.756 0 .268.18.58.688.482A10.019 10.019 0 0022 12c0-5.523-4.477-10-10-10z" />
                                    </svg>
                                </a>

                            </div>
                        </div>
                        <div className='flex flex-col justify-items-center'>
                            <h2>Quick Links</h2>
                            <ul className='text-sm font-extralight mt-2 flex flex-col gap-2'>
                                <li className='hover:underline hover:translate-x-1 transition-transform duration-300'>
                                    <a href="/">Home</a>
                                </li>
                                <li className='hover:underline hover:translate-x-1 transition-transform duration-300'>
                                    <a href="/all-customers">All Customers</a>
                                </li>
                                <li className='hover:underline hover:translate-x-1 transition-transform duration-300'>
                                    <a href="/pending">Pending</a>
                                </li>
                                <li className='hover:underline hover:translate-x-1 transition-transform duration-300'>
                                    <a href="/received">Received</a>
                                </li>
                            </ul>
                        </div>
                        <div className='flex flex-col justify-items-center'>
                            <h2>Contact Us</h2>
                            <p className='text-sm font-extralight mt-2'>Email: <a href="mailto:info@loancollectionagent.com" className='hover:underline'>agrim291104@gmail.com</a></p>
                        </div>
                    </div>

                    <div className='flex flex-wrap flex-col text-sm text-center'>
                        <p className='font-serif'>&copy; {year} Loan Collection Agent. All rights reserved.</p>
                    </div>
                </div>
            </footer>
        </>
    );
}
export default Footer;