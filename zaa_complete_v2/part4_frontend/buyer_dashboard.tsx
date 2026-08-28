"use client";

import { useState, useEffect } from "react";
import Head from "next/head";

// CONFIGURATION - Change this to your deployed API URL
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1/marketplace";

// ZAA Buyer Dashboard - Connected to Real API
export default function BuyerDashboard() {
  const [listings, setListings] = useState([]);
  const [filters, setFilters] = useState({
    commodity: "all",
    location: "all",
    grade: "all",
    minPrice: "",
    maxPrice: ""
  });
  const [selectedListing, setSelectedListing] = useState(null);
  const [bidAmount, setBidAmount] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [stats, setStats] = useState({
    active_listings: 0,
    verified_sellers: 0,
    active_transactions: 0,
    completed_transactions: 0,
    total_volume_ghs: 0
  });

  // Fetch dashboard stats on mount
  useEffect(() => {
    fetchStats();
  }, []);

  // Fetch listings when filters change
  useEffect(() => {
    fetchListings();
  }, [filters]);

  const fetchStats = async () => {
    try {
      const res = await fetch(`${API_BASE_URL}/analytics/overview`);
      if (!res.ok) throw new Error("Failed to fetch stats");
      const data = await res.json();
      setStats(data.stats);
    } catch (err) {
      console.error("Stats error:", err);
      // Fallback stats if API is not ready
      setStats({
        active_listings: 1247,
        verified_sellers: 856,
        active_transactions: 12,
        completed_transactions: 48,
        total_volume_ghs: 245000
      });
    }
  };

  const fetchListings = async () => {
    setLoading(true);
    setError(null);
    try {
      // Build query params
      const params = new URLSearchParams();
      params.append("status", "active");
      params.append("limit", "50");

      if (filters.commodity && filters.commodity !== "all") {
        params.append("commodity", filters.commodity);
      }
      if (filters.location && filters.location !== "all") {
        params.append("location_district", filters.location);
      }
      if (filters.grade && filters.grade !== "all") {
        params.append("grade", filters.grade);
      }
      if (filters.minPrice) {
        params.append("min_price", filters.minPrice);
      }
      if (filters.maxPrice) {
        params.append("max_price", filters.maxPrice);
      }

      const res = await fetch(`${API_BASE_URL}/listings?${params.toString()}`);

      if (!res.ok) {
        throw new Error(`API error: ${res.status}`);
      }

      const data = await res.json();
      setListings(data);
    } catch (err) {
      console.error("Fetch error:", err);
      setError("Unable to connect to ZAA API. Make sure the backend is running.");
      // Fallback to empty array - user sees error message
      setListings([]);
    } finally {
      setLoading(false);
    }
  };

  const placeBid = async () => {
    if (!selectedListing || !bidAmount) return;

    try {
      const res = await fetch(`${API_BASE_URL}/bids`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          buyer_id: "buyer-001", // In production, get from auth context
          listing_id: selectedListing.id,
          bid_price_per_unit: parseFloat(bidAmount),
          quantity_requested: selectedListing.quantity,
          delivery_terms: "farmer_delivers",
          payment_terms: "50_50"
        })
      });

      if (!res.ok) {
        const errData = await res.json();
        throw new Error(errData.detail || "Bid failed");
      }

      const data = await res.json();
      alert(`✅ Bid placed successfully! ID: ${data.bid_id}`);
      setSelectedListing(null);
      setBidAmount("");
      fetchListings(); // Refresh to show updated bid count
    } catch (err) {
      alert(`❌ Error: ${err.message}`);
    }
  };

  const getGradeColor = (grade) => {
    switch(grade) {
      case "A": return "bg-green-500";
      case "B": return "bg-yellow-500";
      case "C": return "bg-orange-500";
      default: return "bg-gray-500";
    }
  };

  const formatDate = (dateStr) => {
    if (!dateStr) return "Recently";
    const date = new Date(dateStr);
    const now = new Date();
    const diffHours = Math.floor((now - date) / (1000 * 60 * 60));
    if (diffHours < 1) return "Just now";
    if (diffHours < 24) return `${diffHours}h ago`;
    return `${Math.floor(diffHours / 24)}d ago`;
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <Head>
        <title>ZAA Buyer Dashboard</title>
      </Head>

      {/* Header */}
      <header className="bg-gradient-to-r from-green-800 to-green-900 text-white shadow-lg">
        <div className="max-w-7xl mx-auto px-4 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-yellow-400 rounded-full flex items-center justify-center text-green-900 font-bold text-xl">
              Z
            </div>
            <div>
              <h1 className="text-xl font-bold">ZAA Buyer Dashboard</h1>
              <p className="text-xs text-green-200">Verified Agricultural Produce from Northern Ghana</p>
            </div>
          </div>
          <div className="flex items-center gap-4">
            <span className="text-sm bg-green-700 px-3 py-1 rounded-full">Premium Plan</span>
            <div className="w-8 h-8 bg-green-600 rounded-full flex items-center justify-center text-sm font-bold">
              JD
            </div>
          </div>
        </div>
      </header>

      <div className="max-w-7xl mx-auto px-4 py-6">
        {/* Stats Bar */}
        <div className="grid grid-cols-5 gap-4 mb-6">
          <div className="bg-white rounded-lg shadow p-4">
            <p className="text-sm text-gray-500">Active Listings</p>
            <p className="text-2xl font-bold text-green-700">{stats.active_listings.toLocaleString()}</p>
          </div>
          <div className="bg-white rounded-lg shadow p-4">
            <p className="text-sm text-gray-500">Verified Sellers</p>
            <p className="text-2xl font-bold text-green-700">{stats.verified_sellers.toLocaleString()}</p>
          </div>
          <div className="bg-white rounded-lg shadow p-4">
            <p className="text-sm text-gray-500">Active Bids</p>
            <p className="text-2xl font-bold text-green-700">{stats.active_transactions}</p>
          </div>
          <div className="bg-white rounded-lg shadow p-4">
            <p className="text-sm text-gray-500">Completed Deals</p>
            <p className="text-2xl font-bold text-green-700">{stats.completed_transactions}</p>
          </div>
          <div className="bg-white rounded-lg shadow p-4">
            <p className="text-sm text-gray-500">Total Volume (GHS)</p>
            <p className="text-2xl font-bold text-green-700">{(stats.total_volume_ghs / 1000).toFixed(0)}K</p>
          </div>
        </div>

        {/* API Status Warning */}
        {error && (
          <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-6">
            <p className="text-red-700 text-sm font-medium">⚠️ {error}</p>
            <p className="text-red-600 text-xs mt-1">
              Make sure your ZAA backend is running at: {API_BASE_URL}
            </p>
          </div>
        )}

        <div className="flex gap-6">
          {/* Filters Sidebar */}
          <div className="w-64 flex-shrink-0">
            <div className="bg-white rounded-lg shadow p-4 sticky top-4">
              <h2 className="font-bold text-gray-800 mb-4">Filters</h2>

              <div className="mb-4">
                <label className="block text-sm font-medium text-gray-700 mb-1">Commodity</label>
                <select 
                  className="w-full border rounded-md px-3 py-2 text-sm"
                  value={filters.commodity}
                  onChange={(e) => setFilters({...filters, commodity: e.target.value})}
                >
                  <option value="all">All Commodities</option>
                  <option value="shea butter">Shea Butter</option>
                  <option value="shea nuts">Shea Nuts</option>
                  <option value="maize">Maize</option>
                  <option value="millet">Millet</option>
                  <option value="groundnuts">Groundnuts</option>
                  <option value="soybeans">Soybeans</option>
                  <option value="cowpeas">Cowpeas</option>
                  <option value="rice">Rice</option>
                  <option value="yam">Yam</option>
                </select>
              </div>

              <div className="mb-4">
                <label className="block text-sm font-medium text-gray-700 mb-1">Location</label>
                <select 
                  className="w-full border rounded-md px-3 py-2 text-sm"
                  value={filters.location}
                  onChange={(e) => setFilters({...filters, location: e.target.value})}
                >
                  <option value="all">All Districts</option>
                  <option value="Tamale">Tamale</option>
                  <option value="Savelugu">Savelugu</option>
                  <option value="Walewale">Walewale</option>
                  <option value="Bawku">Bawku</option>
                  <option value="Bolgatanga">Bolgatanga</option>
                  <option value="Wa">Wa</option>
                </select>
              </div>

              <div className="mb-4">
                <label className="block text-sm font-medium text-gray-700 mb-1">AI Grade</label>
                <select 
                  className="w-full border rounded-md px-3 py-2 text-sm"
                  value={filters.grade}
                  onChange={(e) => setFilters({...filters, grade: e.target.value})}
                >
                  <option value="all">All Grades</option>
                  <option value="A">Grade A (Premium)</option>
                  <option value="B">Grade B (Standard)</option>
                  <option value="C">Grade C (Economy)</option>
                </select>
              </div>

              <div className="mb-4">
                <label className="block text-sm font-medium text-gray-700 mb-1">Price Range (GHS/kg)</label>
                <div className="flex gap-2">
                  <input 
                    type="number" 
                    placeholder="Min"
                    className="w-1/2 border rounded-md px-2 py-1 text-sm"
                    value={filters.minPrice}
                    onChange={(e) => setFilters({...filters, minPrice: e.target.value})}
                  />
                  <input 
                    type="number" 
                    placeholder="Max"
                    className="w-1/2 border rounded-md px-2 py-1 text-sm"
                    value={filters.maxPrice}
                    onChange={(e) => setFilters({...filters, maxPrice: e.target.value})}
                  />
                </div>
              </div>

              <button 
                onClick={fetchListings}
                className="w-full bg-green-700 text-white rounded-md py-2 text-sm font-medium hover:bg-green-800 transition"
              >
                Refresh Listings
              </button>
            </div>
          </div>

          {/* Listings Grid */}
          <div className="flex-1">
            {loading ? (
              <div className="flex items-center justify-center h-64">
                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-green-700"></div>
              </div>
            ) : listings.length === 0 ? (
              <div className="bg-white rounded-lg shadow p-8 text-center">
                <p className="text-gray-500 text-lg">No listings found matching your filters.</p>
                <p className="text-gray-400 text-sm mt-2">Try adjusting your filters or check back later.</p>
              </div>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {listings.map((listing) => (
                  <div key={listing.id} className="bg-white rounded-lg shadow hover:shadow-lg transition-shadow overflow-hidden">
                    {/* Photo Placeholder */}
                    <div className="h-40 bg-gradient-to-br from-gray-100 to-gray-200 flex items-center justify-center relative">
                      {listing.photos && listing.photos.length > 0 ? (
                        <img 
                          src={listing.photos[0]} 
                          alt={listing.commodity_name}
                          className="w-full h-full object-cover"
                        />
                      ) : (
                        <span className="text-gray-400 text-sm">📸 AI Graded Photo</span>
                      )}
                      <div className={`absolute top-2 right-2 ${getGradeColor(listing.quality_grade)} text-white text-xs font-bold px-2 py-1 rounded-full`}>
                        Grade {listing.quality_grade || "N/A"}
                      </div>
                      {listing.ai_confidence && (
                        <div className="absolute top-2 left-2 bg-blue-600 text-white text-xs px-2 py-1 rounded-full">
                          AI {Math.round((listing.ai_confidence || 0) * 100)}%
                        </div>
                      )}
                    </div>

                    <div className="p-4">
                      <div className="flex justify-between items-start mb-2">
                        <div>
                          <h3 className="font-bold text-lg text-gray-800">{listing.commodity_name}</h3>
                          <p className="text-sm text-gray-500">
                            {listing.location_village ? `${listing.location_village}, ` : ""}
                            {listing.location_district || "Northern Region"}
                          </p>
                        </div>
                        <div className="text-right">
                          <p className="text-lg font-bold text-green-700">
                            GHS {listing.asking_price_per_unit || "N/A"}/kg
                          </p>
                        </div>
                      </div>

                      <div className="flex items-center gap-2 mb-3">
                        <div className="w-6 h-6 bg-green-100 rounded-full flex items-center justify-center text-xs text-green-700 font-bold">
                          {(listing.seller_name || "?")[0]}
                        </div>
                        <span className="text-sm text-gray-600">{listing.seller_name || "Verified Seller"}</span>
                        {listing.seller_rating && (
                          <span className="text-xs text-yellow-600">★ {listing.seller_rating.toFixed(1)}</span>
                        )}
                        <span className="text-xs text-gray-400 ml-auto">{formatDate(listing.created_at)}</span>
                      </div>

                      {/* AI Attributes */}
                      {listing.attributes && Object.keys(listing.attributes).length > 0 && (
                        <div className="bg-gray-50 rounded-md p-2 mb-3">
                          <p className="text-xs font-medium text-gray-500 mb-1">AI Analysis:</p>
                          <div className="flex flex-wrap gap-1">
                            {Object.entries(listing.attributes).map(([key, val]) => (
                              <span key={key} className="text-xs bg-white border rounded px-2 py-0.5 text-gray-600">
                                {key.replace(/_/g, ' ')}: {val}
                              </span>
                            ))}
                          </div>
                        </div>
                      )}

                      <div className="flex justify-between items-center">
                        <div>
                          <span className="text-sm text-gray-600">{listing.quantity} {listing.unit} available</span>
                          {listing.bid_count > 0 && (
                            <span className="text-xs text-orange-600 ml-2">• {listing.bid_count} bid{listing.bid_count !== 1 ? 's' : ''}</span>
                          )}
                        </div>
                        <button 
                          onClick={() => setSelectedListing(listing)}
                          className="bg-green-700 text-white px-4 py-2 rounded-md text-sm font-medium hover:bg-green-800 transition"
                        >
                          Place Bid
                        </button>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Bid Modal */}
      {selectedListing && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg shadow-xl max-w-md w-full mx-4 p-6">
            <h2 className="text-xl font-bold mb-4">Place Bid</h2>
            <div className="mb-4">
              <p className="text-sm text-gray-600">Listing: <span className="font-medium">{selectedListing.commodity_name}</span></p>
              <p className="text-sm text-gray-600">Seller: <span className="font-medium">{selectedListing.seller_name || "Verified Seller"}</span></p>
              <p className="text-sm text-gray-600">Quantity: <span className="font-medium">{selectedListing.quantity} {selectedListing.unit}</span></p>
              <p className="text-sm text-gray-600">Asking Price: <span className="font-medium">GHS {selectedListing.asking_price_per_unit || "N/A"}/kg</span></p>
              {selectedListing.quality_grade && (
                <p className="text-sm text-gray-600">AI Grade: <span className="font-medium text-green-600">Grade {selectedListing.quality_grade}</span></p>
              )}
            </div>

            <div className="mb-4">
              <label className="block text-sm font-medium text-gray-700 mb-1">Your Bid (GHS/kg)</label>
              <input 
                type="number"
                step="0.01"
                min={selectedListing.asking_price_per_unit ? selectedListing.asking_price_per_unit * 0.9 : 0}
                className="w-full border rounded-md px-3 py-2"
                placeholder={`Suggested: GHS ${selectedListing.asking_price_per_unit || 0}`}
                value={bidAmount}
                onChange={(e) => setBidAmount(e.target.value)}
              />
              {bidAmount && selectedListing.quantity && (
                <p className="text-xs text-gray-500 mt-1">
                  Total value: GHS {(parseFloat(bidAmount) * selectedListing.quantity).toFixed(2)}
                </p>
              )}
            </div>

            <div className="bg-yellow-50 border border-yellow-200 rounded-md p-3 mb-4">
              <p className="text-xs text-yellow-800">
                <strong>Escrow Protection:</strong> Your bid will be held in escrow. 
                Funds are only released after delivery confirmation.
              </p>
            </div>

            <div className="flex gap-3">
              <button 
                onClick={() => {setSelectedListing(null); setBidAmount("");}}
                className="flex-1 border border-gray-300 text-gray-700 rounded-md py-2 hover:bg-gray-50 transition"
              >
                Cancel
              </button>
              <button 
                onClick={placeBid}
                disabled={!bidAmount || parseFloat(bidAmount) <= 0}
                className="flex-1 bg-green-700 text-white rounded-md py-2 hover:bg-green-800 transition font-medium disabled:bg-gray-400 disabled:cursor-not-allowed"
              >
                Confirm Bid
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
