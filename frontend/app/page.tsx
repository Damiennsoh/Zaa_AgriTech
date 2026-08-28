import Link from "next/link";

export default function Home() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-green-50 to-yellow-50 flex items-center justify-center p-8">
      <div className="max-w-4xl w-full">
        <div className="text-center mb-12">
          <h1 className="text-5xl font-bold text-green-800 mb-4">🌾 ZAA</h1>
          <p className="text-xl text-gray-600">Voice-First AI Agricultural Exchange for Northern Ghana</p>
        </div>

        <div className="grid md:grid-cols-2 gap-8 mb-12">
          <div className="bg-white rounded-xl shadow-lg p-8 border-t-4 border-green-600">
            <h2 className="text-2xl font-bold text-green-700 mb-4">🧑‍🌾 For Farmers</h2>
            <p className="text-gray-600 mb-4">
              ZAA lives in WhatsApp. Just message our phone number to:
            </p>
            <ul className="space-y-2 text-gray-600">
              <li>✅ Check market prices</li>
              <li>✅ List your produce for sale</li>
              <li>✅ Get AI quality grading</li>
              <li>✅ Receive secure payments</li>
            </ul>
            <p className="text-sm text-gray-500 mt-4 italic">No app download required</p>
          </div>

          <div className="bg-white rounded-xl shadow-lg p-8 border-t-4 border-yellow-600">
            <h2 className="text-2xl font-bold text-yellow-700 mb-4">💼 For Buyers</h2>
            <p className="text-gray-600 mb-4">
              Access the buyer dashboard to:
            </p>
            <ul className="space-y-2 text-gray-600">
              <li>✅ Browse AI-graded listings</li>
              <li>✅ Filter by quality and location</li>
              <li>✅ Place secure bids</li>
              <li>✅ Manage escrow payments</li>
            </ul>
            <Link 
              href="/dashboard"
              className="inline-block mt-4 bg-yellow-600 text-white px-6 py-3 rounded-lg font-medium hover:bg-yellow-700 transition"
            >
              Go to Buyer Dashboard →
            </Link>
          </div>
        </div>

        <div className="bg-white rounded-xl shadow-lg p-8">
          <h3 className="text-xl font-bold text-gray-800 mb-4">🚀 Developer Information</h3>
          <div className="grid md:grid-cols-2 gap-6 text-sm">
            <div>
              <h4 className="font-semibold text-gray-700 mb-2">Backend API</h4>
              <p className="text-gray-600">FastAPI server running on port 8000</p>
              <p className="text-gray-600">Endpoints: /api/v1/whatsapp/webhook</p>
            </div>
            <div>
              <h4 className="font-semibold text-gray-700 mb-2">Frontend</h4>
              <p className="text-gray-600">Next.js with TypeScript and Tailwind</p>
              <p className="text-gray-600">Buyer dashboard at /dashboard</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
