export default function SystemPage() {
  return (
    <div className="min-h-[60vh] flex flex-col items-center justify-center px-6 py-12">
      <div className="text-center max-w-md">
        <h1 className="text-4xl font-bold text-gray-900 mb-4">
          System
        </h1>
        <h2 className="text-2xl font-semibold text-gray-600 mb-3">
          Coming Soon
        </h2>
        <p className="text-gray-500 mb-8 leading-relaxed">
          This page is under development and will be available soon.
        </p>
        <a
          href="/announcements"
          className="inline-flex items-center gap-2 px-6 py-3 bg-blue-600 text-white font-medium rounded-lg hover:bg-blue-700 transition-colors duration-200"
        >
          ← Back to Home
        </a>
      </div>
    </div>
  )
}
