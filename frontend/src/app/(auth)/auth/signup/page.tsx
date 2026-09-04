"use client";
import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
export default function Signup() {
  const router = useRouter();
  const [loading, setLoading] = useState(false);
  const handleDemoLogin = () => {
    setLoading(true);
    localStorage.setItem("demo_token", "demo-hackathon-token-123");
    setTimeout(() => router.push("/dashboard"), 500);
  };
  return (
    <div className="min-h-screen bg-zinc-50 flex items-center justify-center p-4">
      <div className="max-w-md w-full bg-white rounded-xl shadow-sm border border-zinc-200 p-8">
        <div className="text-center mb-8">
          <h1 className="text-2xl font-bold">LedgerLens</h1>
          <p className="text-zinc-500">Sign up</p>
        </div>
        <button onClick={handleDemoLogin} className="w-full py-3 bg-blue-50 text-blue-700 rounded-md font-semibold">
          {loading ? "Authenticating..." : "Use Demo Account"}
        </button>
      </div>
    </div>
  );
}