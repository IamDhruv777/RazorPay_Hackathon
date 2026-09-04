import Link from 'next/link'
 
export default function NotFound() {
  return (
    <div className="min-h-screen bg-zinc-50 flex items-center justify-center p-4">
      <div className="text-center">
        <h2 className="text-4xl font-bold text-zinc-900 mb-2">404</h2>
        <p className="text-zinc-500 mb-6">Page not found</p>
        <div className="flex gap-4 justify-center">
            <Link href="/" className="px-4 py-2 bg-white text-zinc-900 border border-zinc-200 rounded-md text-sm font-medium hover:bg-zinc-50 transition-colors">
            Go Home
            </Link>
            <Link href="/dashboard" className="px-4 py-2 bg-zinc-900 text-white rounded-md text-sm font-medium hover:bg-zinc-800 transition-colors">
            Return to Dashboard
            </Link>
        </div>
      </div>
    </div>
  )
}
