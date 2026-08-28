"use client";

import { useState, useEffect } from "react";

// ZAA Buyer Dashboard
// A simple, mobile-first dashboard for buyers to browse listings and place bids

export default function BuyerDashboardClient() {
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
  const [stats, setStats] = useState({
    activeListings: 1247,
    verifiedSellers: 856,
    yourBids: 12,
    completedDeals: 48
  });

  useEffect(() => {
    fetchListings();
    fetchAnalytics();
  }, [filters]);

  const fetchAnalytics = async () => {
    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8002/api/v1/marketplace";
      console.log("Fetching analytics from:", `${apiUrl}/analytics/overview`);
      const res = await fetch(`${apiUrl}/analytics/overview`);
      console.log("Analytics response status:", res.status);

      if (!res.ok) {
        throw new Error(`HTTP error! status: ${res.status}`);
      }

      const data = await res.json();
      setStats({
        activeListings: data.stats.active_listings,
        verifiedSellers: data.stats.verified_sellers,
        yourBids: 12, // This would come from user-specific endpoint
        completedDeals: data.stats.completed_transactions
      });
    } catch (error) {
      console.error("Error fetching analytics:", error);
    }
  };

  const fetchListings = async () => {
    setLoading(true);
    try {
      // Build query parameters
      const params = new URLSearchParams();
      if (filters.commodity !== "all") params.append("commodity", filters.commodity);
      if (filters.location !== "all") params.append("location_district", filters.location);
      if (filters.grade !== "all") params.append("grade", filters.grade);
      if (filters.minPrice) params.append("min_price", filters.minPrice);
      if (filters.maxPrice) params.append("max_price", filters.maxPrice);

      const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8002/api/v1/marketplace";
      console.log("Fetching listings from:", `${apiUrl}/listings?${params.toString()}`);
      const res = await fetch(`${apiUrl}/listings?${params.toString()}`);
      console.log("Response status:", res.status);

      if (!res.ok) {
        throw new Error(`HTTP error! status: ${res.status}`);
      }

      const data = await res.json();

      // Transform API response to match our UI structure
      const transformedListings = data.map((listing: any) => ({
        id: listing.id,
        commodity: listing.commodity_name,
        quantity: listing.quantity,
        unit: listing.unit,
        grade: listing.quality_grade,
        aiConfidence: listing.ai_confidence,
        location: `${listing.location_district}, ${listing.location_village || "Northern Region"}`,
        seller: listing.seller_name || "Unknown",
        sellerRating: listing.seller_rating || 4.0,
        askingPrice: listing.asking_price_per_unit,
        marketPrice: listing.asking_price_per_unit * 1.2, // 20% market markup
        photoUrl: "/api/placeholder/300/200",
        listedAt: "Recently",
        attributes: listing.attributes || {}
      }));

      setListings(transformedListings);
    } catch (error) {
      console.error("Error fetching listings:", error);
      // Fallback to mock data if API fails
      const mockListings = [
        {
          id: "a3b7c9d2",
          commodity: "Shea Butter",
          quantity: 50,
          unit: "kg",
          grade: "A",
          aiConfidence: 0.92,
          location: "Savelugu, Northern Region",
          seller: "Amina Y.",
          sellerRating: 4.8,
          askingPrice: 10,
          marketPrice: 12,
          photoUrl: "/api/placeholder/300/200",
          listedAt: "2 hours ago",
          attributes: { color: "ivory_white", texture: "smooth", smell: "nutty" }
        }
      ];
      setListings(mockListings);
    } finally {
      setLoading(false);
    }
  };

  const placeBid = async () => {
    if (!selectedListing || !bidAmount) return;

    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8002/api/v1/marketplace";
      const res = await fetch(`${apiUrl}/bids`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify({
          buyer_id: "demo_buyer_123", // In production, get from auth
          listing_id: selectedListing.id,
          bid_price_per_unit: parseFloat(bidAmount),
          quantity_requested: selectedListing.quantity,
          delivery_terms: "farmer_delivers",
          payment_terms: "50_50"
        })
      });

      const data = await res.json();

      if (res.ok) {
        alert(`Bid of GHS ${bidAmount}/kg placed on ${selectedListing.commodity} from ${selectedListing.seller}!`);
        setSelectedListing(null);
        setBidAmount("");
      } else {
        alert(`Failed to place bid: ${data.detail || "Unknown error"}`);
      }
    } catch (error) {
      console.error("Error placing bid:", error);
      alert(`Failed to place bid: ${error.message}`);
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

  return (
    <div className="min-h-screen bg-gray-50">
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
        <div className="grid grid-cols-4 gap-4 mb-6">
          <div className="bg-white rounded-lg shadow p-4">
            <p className="text-sm text-gray-500">Active Listings</p>
            <p className="text-2xl font-bold text-green-700">{stats.activeListings.toLocaleString()}</p>
          </div>
          <div className="bg-white rounded-lg shadow p-4">
            <p className="text-sm text-gray-500">Verified Sellers</p>
            <p className="text-2xl font-bold text-green-700">{stats.verifiedSellers.toLocaleString()}</p>
          </div>
          <div className="bg-white rounded-lg shadow p-4">
            <p className="text-sm text-gray-500">Your Bids</p>
            <p className="text-2xl font-bold text-green-700">{stats.yourBids}</p>
          </div>
          <div className="bg-white rounded-lg shadow p-4">
            <p className="text-sm text-gray-500">Completed Deals</p>
            <p className="text-2xl font-bold text-green-700">{stats.completedDeals}</p>
          </div>
        </div>

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
                  <option value="shea_butter">Shea Butter</option>
                  <option value="shea_nuts">Shea Nuts</option>
                  <option value="maize">Maize</option>
                  <option value="millet">Millet</option>
                  <option value="groundnuts">Groundnuts</option>
                  <option value="soybeans">Soybeans</option>
                  <option value="cowpeas">Cowpeas</option>
                </select>
              </div>

              <div className="mb-4">
                <label className="block text-sm font-medium text-gray-700 mb-1">Location</label>
                <select 
                  className="w-full border rounded-md px-3 py-2 text-sm"
                  value={filters.location}
                  onChange={(e) => setFilters({...filters, location: e.target.value})}
                >
                  <option value="all">All Regions</option>
                  <option value="northern">Northern Region</option>
                  <option value="savannah">Savannah Region</option>
                  <option value="northeast">North East Region</option>
                  <option value="uppereast">Upper East Region</option>
                  <option value="upperwest">Upper West Region</option>
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
                Apply Filters
              </button>
            </div>
          </div>

          {/* Listings Grid */}
          <div className="flex-1">
            {loading ? (
              <div className="flex items-center justify-center h-64">
                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-green-700"></div>
              </div>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {listings.map((listing) => (
                  <div key={listing.id} className="bg-white rounded-lg shadow hover:shadow-lg transition-shadow overflow-hidden">
                    {/* Photo Placeholder */}
                    <div className="h-40 bg-gray-200 flex items-center justify-center relative">
                      <span className="text-gray-400 text-sm">AI Graded Photo</span>
                      <div className={`absolute top-2 right-2 ${getGradeColor(listing.grade)} text-white text-xs font-bold px-2 py-1 rounded-full`}>
                        Grade {listing.grade}
                      </div>
                      <div className="absolute top-2 left-2 bg-blue-600 text-white text-xs px-2 py-1 rounded-full">
                        AI {Math.round(listing.aiConfidence * 100)}%
                      </div>
                    </div>

                    <div className="p-4">
                      <div className="flex justify-between items-start mb-2">
                        <div>
                          <h3 className="font-bold text-lg text-gray-800">{listing.commodity}</h3>
                          <p className="text-sm text-gray-500">{listing.location}</p>
                        </div>
                        <div className="text-right">
                          <p className="text-lg font-bold text-green-700">GHS {listing.askingPrice}/kg</p>
                          <p className="text-xs text-gray-400">Market: GHS {listing.marketPrice}/kg</p>
                        </div>
                      </div>

                      <div className="flex items-center gap-2 mb-3">
                        <div className="w-6 h-6 bg-gray-300 rounded-full flex items-center justify-center text-xs">
                          {listing.seller[0]}
                        </div>
                        <span className="text-sm text-gray-600">{listing.seller}</span>
                        <span className="text-xs text-yellow-600">★ {listing.sellerRating}</span>
                        <span className="text-xs text-gray-400 ml-auto">{listing.listedAt}</span>
                      </div>

                      {/* AI Attributes */}
                      <div className="bg-gray-50 rounded-md p-2 mb-3">
                        <p className="text-xs font-medium text-gray-500 mb-1">AI Analysis:</p>
                        <div className="flex flex-wrap gap-1">
                          {Object.entries(listing.attributes).map(([key, val]) => (
                            <span key={key} className="text-xs bg-white border rounded px-2 py-0.5 text-gray-600">
                              {key.replace('_', ' ')}: {val}
                            </span>
                          ))}
                        </div>
                      </div>

                      <div className="flex justify-between items-center">
                        <span className="text-sm text-gray-600">{listing.quantity} {listing.unit} available</span>
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
              <p className="text-sm text-gray-600">Listing: <span className="font-medium">{selectedListing.commodity}</span></p>
              <p className="text-sm text-gray-600">Seller: <span className="font-medium">{selectedListing.seller}</span></p>
              <p className="text-sm text-gray-600">Quantity: <span className="font-medium">{selectedListing.quantity} {selectedListing.unit}</span></p>
              <p className="text-sm text-gray-600">Asking Price: <span className="font-medium">GHS {selectedListing.askingPrice}/kg</span></p>
            </div>

            <div className="mb-4">
              <label className="block text-sm font-medium text-gray-700 mb-1">Your Bid (GHS/kg)</label>
              <input 
                type="number"
                className="w-full border rounded-md px-3 py-2"
                placeholder={`Min: GHS ${selectedListing.askingPrice * 0.9}`}
                value={bidAmount}
                onChange={(e) => setBidAmount(e.target.value)}
              />
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
                className="flex-1 bg-green-700 text-white rounded-md py-2 hover:bg-green-800 transition font-medium"
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
