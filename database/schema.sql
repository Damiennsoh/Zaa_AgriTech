
-- ============================================================
-- ZAA DATABASE SCHEMA v1.0
-- The Voice-First AI Agricultural Exchange for Northern Ghana
-- PostgreSQL + Supabase Compatible
-- ============================================================

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS postgis;

-- ============================================================
-- 1. USERS & PROFILES
-- ============================================================

CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    phone_number VARCHAR(20) UNIQUE NOT NULL,  -- WhatsApp number is the identity
    display_name VARCHAR(100),
    user_type VARCHAR(20) NOT NULL CHECK (user_type IN ('farmer', 'buyer', 'cooperative', 'admin')),
    preferred_language VARCHAR(10) DEFAULT 'dag',  -- dag=Dagbani, tw=Tw, gon=Gonja, ha=Hausa, en=English
    location_region VARCHAR(50),  -- Northern, Savannah, North East, Upper East, Upper West
    location_district VARCHAR(50),  -- Tamale, Savelugu, Walewale, Bolgatanga, etc.
    location_village VARCHAR(100),
    gps_latitude DECIMAL(10, 8),
    gps_longitude DECIMAL(11, 8),
    verification_status VARCHAR(20) DEFAULT 'pending' CHECK (verification_status IN ('pending', 'verified', 'rejected', 'suspended')),
    verification_method VARCHAR(50),  -- ghana_card, community_reference, cooperative_member
    ghana_card_number VARCHAR(20),
    moMo_wallet VARCHAR(20),  -- MTN MoMo number for payments
    profile_photo_url TEXT,
    bio TEXT,
    years_in_farming INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_active_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    is_active BOOLEAN DEFAULT TRUE
);

CREATE INDEX idx_users_phone ON users(phone_number);
CREATE INDEX idx_users_location ON users(location_district, location_region);
CREATE INDEX idx_users_type ON users(user_type);

-- ============================================================
-- 2. COMMODITIES & PRODUCTS
-- ============================================================

CREATE TABLE commodities (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name_en VARCHAR(100) NOT NULL,           -- English name
    name_dag VARCHAR(100),                    -- Dagbani name
    name_tw VARCHAR(100),                     -- Twi name
    name_gon VARCHAR(100),                    -- Gonja name
    category VARCHAR(50) NOT NULL,            -- shea, cereals, legumes, vegetables, livestock
    subcategory VARCHAR(50),                  -- shea_nuts, shea_butter, maize, millet, groundnuts, etc.
    grading_criteria JSONB,                   -- AI grading parameters (color, texture, moisture, etc.)
    standard_unit VARCHAR(20) DEFAULT 'kg',   -- kg, bag_85kg, bag_50kg, litre, piece
    shelf_life_days INTEGER,
    storage_requirements TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Seed commodities for Northern Ghana
INSERT INTO commodities (name_en, name_dag, name_tw, category, subcategory, grading_criteria) VALUES
('Shea Nuts', 'Kpakpi', 'Shea', 'shea', 'shea_nuts', '{"color": ["brown", "light_brown", "grey"], "size": ["large", "medium", "small"], "moisture_max": 8}'),
('Shea Butter', 'Kpakpi Nu', 'Shea Butter', 'shea', 'shea_butter', '{"color": ["ivory_white", "cream", "yellowish", "grey"], "texture": ["smooth", "grainy", "crumbly"], "smell": ["nutty", "smoky", "rancid"]}'),
('Maize', 'Kpaligu', 'Aburoo', 'cereals', 'maize', '{"color": ["yellow", "white", "mixed"], "moisture_max": 13, "damaged_max_pct": 5}'),
('Millet', 'Kosaa', 'Millet', 'cereals', 'millet', '{"color": ["white", "grey", "brown"], "moisture_max": 12}'),
('Groundnuts', 'Simitoo', 'Nkatee', 'legumes', 'groundnuts', '{"size": ["large", "medium", "small"], "shell_condition": ["intact", "broken"], "aflatoxin_ppb_max": 20}'),
('Soybeans', 'Soya', 'Soya', 'legumes', 'soybeans', '{"color": ["yellow", "brown"], "moisture_max": 13}'),
('Rice', 'Mui', 'Emo', 'cereals', 'rice', '{"grain_type": ["long", "medium", "short"], "moisture_max": 14}'),
('Cowpeas', 'Bewa', 'Aduwa', 'legumes', 'cowpeas', '{"color": ["white", "brown", "black"], "size": ["large", "medium", "small"]}'),
('Yam', 'Kpihili', 'Bayere', 'tubers', 'yam', '{"size": ["large", "medium", "small"], "variety": ["pona", "lariboko", "dente"]}'),
('Live Chicken', 'Kpini', 'Akokonini', 'livestock', 'poultry', '{"weight_kg_min": 1.5, "health_status": ["healthy", "sick"]}');

-- ============================================================
-- 3. MARKET PRICES (Real-time & Historical)
-- ============================================================

CREATE TABLE market_prices (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    commodity_id UUID REFERENCES commodities(id),
    market_location VARCHAR(100) NOT NULL,      -- Tamale Central Market, Walewale Market, etc.
    market_type VARCHAR(20) DEFAULT 'local' CHECK (market_type IN ('local', 'regional', 'national', 'export')),
    price_per_unit DECIMAL(12, 2) NOT NULL,     -- in GHS
    unit VARCHAR(20) NOT NULL,                  -- kg, bag_85kg, etc.
    quality_grade VARCHAR(10),                  -- A, B, C, or premium, standard, reject
    price_date DATE NOT NULL DEFAULT CURRENT_DATE,
    source VARCHAR(50),                         -- manual_survey, farmer_report, buyer_report, ai_estimate
    collected_by UUID REFERENCES users(id),     -- if collected by a user
    confidence_score DECIMAL(3, 2),             -- 0.0 to 1.0, AI confidence if estimated
    is_verified BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_prices_commodity ON market_prices(commodity_id);
CREATE INDEX idx_prices_location ON market_prices(market_location);
CREATE INDEX idx_prices_date ON market_prices(price_date DESC);

-- ============================================================
-- 4. LISTINGS (What farmers are selling)
-- ============================================================

CREATE TABLE listings (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    seller_id UUID REFERENCES users(id),
    commodity_id UUID REFERENCES commodities(id),
    quantity DECIMAL(10, 2) NOT NULL,
    unit VARCHAR(20) NOT NULL,
    quality_grade VARCHAR(10),                  -- AI-assigned after photo grading
    ai_confidence DECIMAL(3, 2),                -- AI confidence in grade
    asking_price_per_unit DECIMAL(12, 2),       -- Farmer's asking price (optional)
    description TEXT,                           -- Voice-to-text description
    description_audio_url TEXT,               -- Original voice note URL
    photos JSONB,                             -- Array of photo URLs
    location_region VARCHAR(50),
    location_district VARCHAR(50),
    location_village VARCHAR(100),
    gps_latitude DECIMAL(10, 8),
    gps_longitude DECIMAL(11, 8),
    status VARCHAR(20) DEFAULT 'active' CHECK (status IN ('draft', 'active', 'negotiating', 'sold', 'expired', 'withdrawn')),
    expiry_date DATE,                           -- Auto-expire after 14 days
    is_group_listing BOOLEAN DEFAULT FALSE,     -- Part of a group sale?
    group_id UUID,                              -- If group listing
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_listings_seller ON listings(seller_id);
CREATE INDEX idx_listings_commodity ON listings(commodity_id);
CREATE INDEX idx_listings_status ON listings(status);
CREATE INDEX idx_listings_location ON listings(location_district, location_region);

-- ============================================================
-- 5. AI GRADING RESULTS
-- ============================================================

CREATE TABLE ai_grading_results (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    listing_id UUID REFERENCES listings(id),
    photo_url TEXT NOT NULL,
    commodity_id UUID REFERENCES commodities(id),
    ai_model VARCHAR(50),                     -- yolo_shea, resnet_commodity, etc.
    grade VARCHAR(10),                        -- A, B, C
    confidence DECIMAL(3, 2),
    attributes JSONB,                         -- {"color": "ivory_white", "texture": "smooth", "impurities_pct": 2}
    estimated_value_per_unit DECIMAL(12, 2),  -- AI-estimated fair market value
    market_comparison JSONB,                  -- {"local_avg": 450, "regional_avg": 520, "export_avg": 800}
    processing_time_ms INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ============================================================
-- 6. BIDS & NEGOTIATIONS
-- ============================================================

CREATE TABLE bids (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    listing_id UUID REFERENCES listings(id),
    buyer_id UUID REFERENCES users(id),
    bid_price_per_unit DECIMAL(12, 2) NOT NULL,
    total_bid_value DECIMAL(12, 2) NOT NULL,
    quantity_requested DECIMAL(10, 2),
    unit VARCHAR(20),
    delivery_terms VARCHAR(50),               -- farmer_delivers, buyer_collects, meet_halfway
    payment_terms VARCHAR(50),                  -- full_upfront, 50_50, pay_on_delivery
    delivery_date DATE,
    status VARCHAR(20) DEFAULT 'pending' CHECK (status IN ('pending', 'accepted', 'rejected', 'countered', 'expired')),
    buyer_message TEXT,
    farmer_response TEXT,
    ai_negotiation_suggestion TEXT,           -- AI suggests whether to accept/counter
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_bids_listing ON bids(listing_id);
CREATE INDEX idx_bids_buyer ON bids(buyer_id);

-- ============================================================
-- 7. TRANSACTIONS & ESCROW
-- ============================================================

CREATE TABLE transactions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    bid_id UUID REFERENCES bids(id),
    listing_id UUID REFERENCES listings(id),
    seller_id UUID REFERENCES users(id),
    buyer_id UUID REFERENCES users(id),
    commodity_id UUID REFERENCES commodities(id),
    quantity DECIMAL(10, 2) NOT NULL,
    unit VARCHAR(20),
    agreed_price_per_unit DECIMAL(12, 2) NOT NULL,
    total_value DECIMAL(12, 2) NOT NULL,
    platform_fee DECIMAL(12, 2),                -- 2% from buyer
    seller_receives DECIMAL(12, 2),             -- Total minus platform fee
    status VARCHAR(30) DEFAULT 'pending' CHECK (status IN (
        'pending', 'deposit_received', 'in_transit', 
        'delivered', 'confirmed', 'disputed', 'completed', 'cancelled', 'refunded'
    )),
    escrow_status VARCHAR(20) DEFAULT 'pending' CHECK (escrow_status IN ('pending', 'held', 'released', 'refunded')),
    deposit_amount DECIMAL(12, 2),
    deposit_momo_transaction_id VARCHAR(100),
    final_payment_amount DECIMAL(12, 2),
    final_momo_transaction_id VARCHAR(100),
    delivery_tracking JSONB,                    -- {"pickup_time": "...", "delivery_time": "...", "carrier": "..."}
    dispute_reason TEXT,
    dispute_resolution TEXT,
    completed_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ============================================================
-- 8. CONVERSATIONS (WhatsApp Message History)
-- ============================================================

CREATE TABLE conversations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id),
    wa_message_id VARCHAR(100),
    direction VARCHAR(10) CHECK (direction IN ('inbound', 'outbound')),
    message_type VARCHAR(20) CHECK (message_type IN ('text', 'audio', 'image', 'document', 'location', 'button', 'interactive')),
    content_text TEXT,
    content_audio_url TEXT,
    content_image_url TEXT,
    detected_language VARCHAR(10),              -- dag, tw, gon, en
    translated_text TEXT,                     -- English translation for AI processing
    ai_intent VARCHAR(50),                    -- price_check, list_product, grade_photo, place_bid, etc.
    ai_confidence DECIMAL(3, 2),
    ai_response_text TEXT,
    ai_response_audio_url TEXT,
    ai_response_language VARCHAR(10),         -- Language of response
    processing_time_ms INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_conversations_user ON conversations(user_id);
CREATE INDEX idx_conversations_created ON conversations(created_at DESC);

-- ============================================================
-- 9. GROUP SELLING (AI-Coordinated Cooperatives)
-- ============================================================

CREATE TABLE selling_groups (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(100),
    commodity_id UUID REFERENCES commodities(id),
    location_district VARCHAR(50),
    location_village VARCHAR(100),
    total_quantity DECIMAL(10, 2) DEFAULT 0,
    unit VARCHAR(20),
    target_price_per_unit DECIMAL(12, 2),
    ai_suggested_premium_pct DECIMAL(5, 2),   -- e.g., 25% above individual price
    status VARCHAR(20) DEFAULT 'forming' CHECK (status IN ('forming', 'negotiating', 'sold', 'cancelled')),
    coordinator_id UUID REFERENCES users(id), -- Usually the AI or a lead farmer
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    deadline DATE                             -- Group closes on this date
);

CREATE TABLE group_members (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    group_id UUID REFERENCES selling_groups(id),
    farmer_id UUID REFERENCES users(id),
    quantity_contributed DECIMAL(10, 2),
    unit VARCHAR(20),
    contribution_percentage DECIMAL(5, 2),  -- For revenue splitting
    status VARCHAR(20) DEFAULT 'committed' CHECK (status IN ('committed', 'delivered', 'paid', 'withdrawn')),
    joined_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ============================================================
-- 10. BUYER SUBSCRIPTIONS
-- ============================================================

CREATE TABLE buyer_subscriptions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    buyer_id UUID REFERENCES users(id),
    tier VARCHAR(20) CHECK (tier IN ('free', 'basic', 'premium', 'enterprise')),
    price_per_month DECIMAL(12, 2),
    features JSONB,                           -- {"ai_grading": true, "bulk_matching": true, "api_access": true}
    starts_at TIMESTAMP WITH TIME ZONE,
    expires_at TIMESTAMP WITH TIME ZONE,
    payment_status VARCHAR(20) DEFAULT 'active' CHECK (payment_status IN ('active', 'cancelled', 'expired', 'past_due')),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ============================================================
-- 11. NOTIFICATIONS
-- ============================================================

CREATE TABLE notifications (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id),
    type VARCHAR(50),                         -- price_alert, new_bid, group_opportunity, delivery_reminder
    title VARCHAR(200),
    body TEXT,
    data JSONB,                               -- {"listing_id": "...", "bid_id": "..."}
    channel VARCHAR(20) DEFAULT 'whatsapp' CHECK (channel IN ('whatsapp', 'sms', 'voice_call', 'dashboard')),
    language VARCHAR(10),
    sent_at TIMESTAMP WITH TIME ZONE,
    read_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ============================================================
-- VIEWS FOR ANALYTICS
-- ============================================================

CREATE VIEW v_daily_prices AS
SELECT 
    commodity_id,
    market_location,
    DATE(price_date) as date,
    AVG(price_per_unit) as avg_price,
    MIN(price_per_unit) as min_price,
    MAX(price_per_unit) as max_price,
    COUNT(*) as sample_count
FROM market_prices
GROUP BY commodity_id, market_location, DATE(price_date);

CREATE VIEW v_farmer_income AS
SELECT 
    u.id as farmer_id,
    u.display_name,
    u.location_district,
    COUNT(t.id) as total_sales,
    SUM(t.seller_receives) as total_earnings,
    AVG(t.agreed_price_per_unit) as avg_price_received
FROM users u
LEFT JOIN transactions t ON u.id = t.seller_id AND t.status = 'completed'
WHERE u.user_type = 'farmer'
GROUP BY u.id, u.display_name, u.location_district;

-- ============================================================
-- TRIGGERS
-- ============================================================

CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_listings_updated_at BEFORE UPDATE ON listings
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_bids_updated_at BEFORE UPDATE ON bids
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ============================================================
-- END OF SCHEMA
-- ============================================================
