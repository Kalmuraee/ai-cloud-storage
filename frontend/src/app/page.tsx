export default function Home() {
  return (
    <div className="flex min-h-screen flex-col items-center justify-center p-24">
      <div className="z-10 max-w-5xl w-full items-center justify-between font-mono text-sm">
        <h1 className="text-4xl font-bold text-center mb-8">
          AI Cloud Storage Platform
        </h1>
        <p className="text-center text-lg mb-4">
          Intelligent cloud storage with advanced AI capabilities
        </p>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 mt-8">
          <div className="border border-gray-200 rounded-lg p-6 hover:shadow-lg transition-shadow">
            <h2 className="text-xl font-semibold mb-2">Smart Storage</h2>
            <p>Store and manage your files with AI-powered organization</p>
          </div>
          <div className="border border-gray-200 rounded-lg p-6 hover:shadow-lg transition-shadow">
            <h2 className="text-xl font-semibold mb-2">Intelligent Search</h2>
            <p>Find content quickly with advanced semantic search</p>
          </div>
          <div className="border border-gray-200 rounded-lg p-6 hover:shadow-lg transition-shadow">
            <h2 className="text-xl font-semibold mb-2">AI Processing</h2>
            <p>Automatic content analysis and processing</p>
          </div>
        </div>
      </div>
    </div>
  )
}