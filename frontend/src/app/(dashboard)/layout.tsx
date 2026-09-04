'use client';

import { useEffect, useState } from 'react';
import { useRouter, usePathname } from 'next/navigation';
import Link from 'next/link';
import dynamic from 'next/dynamic';
const UserCursor = dynamic(() => import('@/components/effects/UserCursor'), { ssr: false });
import { 
  LayoutDashboard, AlertCircle, RefreshCw, BarChart, 
  ShieldAlert, FileText, Briefcase, Network, Zap, 
  CheckCircle, Search, Bell, User, LogOut, Settings, Building, Clock
} from 'lucide-react';

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const pathname = usePathname();
  const [authed, setAuthed] = useState(false);

  useEffect(() => {
    const token = localStorage.getItem('demo_token');
    if (!token && !pathname.includes('/auth')) {
      router.push('/auth/login');
    } else {
      setAuthed(true);
    }
  }, [pathname, router]);

  if (!authed) return <div className="h-screen bg-zinc-50 flex items-center justify-center text-zinc-500 animate-pulse">Initializing Control Center...</div>;

  const NavItem = ({ href, icon: Icon, label }: { href: string, icon: any, label: string }) => {
    const active = pathname === href || pathname.startsWith(href + '/');
    return (
      <Link 
        href={href} 
        className={`flex items-center gap-3 px-3 py-2 rounded-lg transition-all text-sm font-medium ${
          active 
            ? 'bg-zinc-800 text-white shadow-sm' 
            : 'text-zinc-400 hover:bg-zinc-800/50 hover:text-zinc-200'
        }`}
      >
        <Icon className={`h-4 w-4 ${active ? 'text-blue-400' : 'text-zinc-400'}`} />
        {label}
      </Link>
    );
  };

  return (
    <div className="flex h-screen bg-zinc-50 font-sans overflow-hidden text-zinc-900">
      
      {/* Sidebar - Dark Premium */}
      <aside className="w-64 bg-zinc-950 text-white flex flex-col border-r border-zinc-900 shadow-xl z-20 flex-shrink-0">
        <div className="p-5">
          <Link href="/dashboard" className="flex items-center gap-2">
            <div className="w-5 h-5 rounded-full bg-blue-500 shadow-[0_0_15px_rgba(59,130,246,0.5)]" />
            <span className="text-xl font-semibold tracking-tight text-white">LedgerLens</span>
          </Link>
          <div className="mt-4 flex items-center gap-2 px-3 py-2 bg-zinc-900 rounded-lg border border-zinc-800">
            <Building className="w-4 h-4 text-zinc-400" />
            <span className="text-xs font-medium text-zinc-300">Acme Corp</span>
          </div>
        </div>
        
        <nav className="flex-1 px-3 space-y-6 mt-2 overflow-y-auto custom-scrollbar pb-8">
          
          <div>
            <div className="text-[10px] font-bold text-zinc-500 mb-2 px-3 uppercase tracking-widest">Overview</div>
            <div className="space-y-1">
              <NavItem href="/dashboard" icon={LayoutDashboard} label="Dashboard" />
              <NavItem href="/transactions" icon={FileText} label="Transactions" />
              <NavItem href="/close-readiness" icon={Briefcase} label="Close Readiness" />
            </div>
          </div>

          <div>
            <div className="text-[10px] font-bold text-zinc-500 mb-2 px-3 uppercase tracking-widest">Investigation</div>
            <div className="space-y-1">
              <NavItem href="/exceptions" icon={AlertCircle} label="Exception Queue" />
              <NavItem href="/incidents" icon={BarChart} label="What Changed?" />
              <NavItem href="/root-causes" icon={Network} label="Root Causes" />
            </div>
          </div>

          <div>
            <div className="text-[10px] font-bold text-zinc-500 mb-2 px-3 uppercase tracking-widest">Prevention</div>
            <div className="space-y-1">
              <NavItem href="/early-warnings" icon={ShieldAlert} label="Early Warnings" />
              <NavItem href="/priority" icon={Zap} label="Priority Queue" />
            </div>
          </div>

          <div>
            <div className="text-[10px] font-bold text-zinc-500 mb-2 px-3 uppercase tracking-widest">System</div>
            <div className="space-y-1">
              <NavItem href="/evaluation" icon={CheckCircle} label="Evaluation" />
              <NavItem href="/simulate" icon={RefreshCw} label="Simulator" />
            </div>
          </div>
        </nav>

        <div className="p-4 border-t border-zinc-900 space-y-1">
          <button className="w-full flex items-center gap-3 px-3 py-2 text-zinc-400 hover:text-white hover:bg-zinc-900 rounded-lg text-sm transition-colors">
            <Settings className="w-4 h-4" /> Settings
          </button>
          <button 
            onClick={() => { localStorage.removeItem('demo_token'); router.push('/auth/login'); }} 
            className="w-full flex items-center gap-3 px-3 py-2 text-zinc-400 hover:text-white hover:bg-zinc-900 rounded-lg text-sm transition-colors"
          >
            <LogOut className="w-4 h-4" /> Sign Out
          </button>
        </div>
      </aside>

      {/* Main Content Area */}
      <div className="flex-1 flex flex-col min-w-0 overflow-hidden">
        
        {/* Global Header */}
        <header className="h-16 bg-white border-b border-zinc-200 flex items-center justify-between px-8 z-10 flex-shrink-0">
          <div className="flex items-center gap-4">
            <div className="flex items-center gap-2 text-xs font-medium text-emerald-600 bg-emerald-50 px-2.5 py-1 rounded-full border border-emerald-200">
              <div className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
              System Active
            </div>
            <div className="flex items-center gap-1.5 text-xs text-zinc-500">
              <Clock className="w-3.5 h-3.5" />
              Last reconciled 4 mins ago
            </div>
          </div>
          
          <div className="flex items-center gap-6">
            <div className="relative">
              <Search className="w-4 h-4 text-zinc-400 absolute left-3 top-1/2 -translate-y-1/2" />
              <input 
                type="text" 
                placeholder="Search transactions, exceptions..." 
                className="pl-9 pr-4 py-1.5 bg-zinc-100 border-transparent rounded-full text-sm focus:bg-white focus:border-blue-500 focus:ring-2 focus:ring-blue-200 transition-all w-64 outline-none"
              />
            </div>
            
            <div className="flex items-center gap-4">
              <button className="relative text-zinc-400 hover:text-zinc-600 transition-colors">
                <Bell className="w-5 h-5" />
                <span className="absolute 0 right-0 w-2 h-2 bg-red-500 rounded-full border-2 border-white" />
              </button>
              <button className="w-8 h-8 rounded-full bg-zinc-200 border border-zinc-300 flex items-center justify-center text-zinc-600 hover:bg-zinc-300 transition-colors">
                <User className="w-4 h-4" />
              </button>
            </div>
          </div>
        </header>

        {/* Page Content */}
        <main className="flex-1 overflow-y-auto">
          {children}
        </main>
      </div>
      <UserCursor label="Finance" />
    </div>
  );
}
