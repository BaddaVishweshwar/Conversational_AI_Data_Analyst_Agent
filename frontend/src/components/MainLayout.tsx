import React from 'react';
import Sidebar from './Sidebar';

interface MainLayoutProps {
    children: React.ReactNode;
}

export default function MainLayout({ children }: MainLayoutProps) {
    return (
        <div className="flex bg-white text-slate-900 min-h-screen overflow-hidden font-sans">
            <Sidebar />
            <main className="flex-1 h-screen overflow-y-auto relative custom-scrollbar bg-slate-50/50">
                <div className="relative z-10 p-6 md:p-8 lg:p-10 max-w-[1600px] mx-auto w-full">
                    {children}
                </div>
            </main>
        </div>
    );
}
