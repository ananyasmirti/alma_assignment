import Link from "next/link";

export default function Home() {
  return (
    <main className="flex min-h-screen flex-col items-center justify-center p-8">
      <div className="text-center space-y-6 max-w-lg">
        <h1 className="text-4xl font-bold text-gray-900">Alma</h1>
        <p className="text-lg text-gray-600">Immigration Law Lead Management</p>
        <div className="flex gap-4 justify-center">
          <Link
            href="/apply"
            className="px-6 py-3 bg-blue-600 text-white rounded-lg font-medium hover:bg-blue-700 transition-colors"
          >
            Apply Now
          </Link>
          <Link
            href="/login"
            className="px-6 py-3 border border-gray-300 text-gray-700 rounded-lg font-medium hover:bg-gray-100 transition-colors"
          >
            Attorney Login
          </Link>
        </div>
      </div>
    </main>
  );
}
