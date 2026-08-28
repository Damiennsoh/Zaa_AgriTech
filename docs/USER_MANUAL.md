# ZAA User Manual
## Complete Guide for Farmers and Buyers

---

## 📱 Table of Contents
1. [System Overview](#system-overview)
2. [For Farmers: Using ZAA via WhatsApp](#for-farmers-using-zaa-via-whatsapp)
3. [For Buyers: Using the Web Dashboard](#for-buyers-using-the-web-dashboard)
4. [Complete Transaction Flow](#complete-transaction-flow)
5. [Notification System](#notification-system)
6. [Payment & Escrow Process](#payment--escrow-process)
7. [Dispute Resolution](#dispute-resolution)
8. [Frequently Asked Questions](#frequently-asked-questions)

---

## System Overview

ZAA is an AI-powered agricultural trading platform with two different interfaces:

### 🧑‍🌾 For Farmers (WhatsApp Interface)
- **What you need**: Regular WhatsApp app on your phone
- **What you do**: Send voice notes, text messages, and photos
- **What you don't need**: No app download, no password, no website access
- **Languages supported**: Dagbani, Twi, Gonja, Hausa, English

### 💼 For Buyers (Web Dashboard)
- **What you need**: Laptop, tablet, or smartphone with web browser
- **What you do**: Browse listings, filter by quality, place bids, manage transactions
- **What you don't need**: WhatsApp account, phone number verification
- **Language**: English

### 🔄 How They Connect
Farmers and buyers **never interact directly**. ZAA acts as the trusted middleman that:
- Translates between languages
- Grades quality with AI
- Holds money in escrow
- Tracks delivery
- Resolves disputes

---

## For Farmers: Using ZAA via WhatsApp

### Getting Started

1. **Save ZAA's Phone Number**
   - Add `+233 55 123 4567` to your WhatsApp contacts
   - Name it "ZAA" or "ZAA Agricultural"

2. **Send Your First Message**
   - Open a chat with ZAA
   - Send a voice note: "Naa, I want to sell my produce"
   - ZAA will guide you through the process

### Creating a Listing

**Step 1: List Your Produce**
```
Voice: "Naa, I have 50kg of shea butter. I want to sell."
```
ZAA will respond:
```
✅ Great! I've listed your 50kg of shea butter.
Listing ID: #A3B7C9D2
Status: Active
Expiry: 14 days

📸 Send me a photo and I'll grade the quality to help you get the best price!
```

**Step 2: Get AI Quality Grading**
- Take a clear photo of your produce
- Send it to ZAA via WhatsApp
- ZAA will analyze it and reply:
```
📸 AI Quality Grading Result:

Grade: ⭐⭐⭐⭐ A
Confidence: 92%

Details:
• Color: ivory_white
• Texture: smooth
• Smell: nutty

💰 Estimated Fair Value: ₵12/kg
Local market average: ₵6/kg
Export market potential: ₵18/kg

🌟 Excellent quality! You can command premium prices.
```

**Step 3: Wait for Bids**
- Your listing appears on buyer dashboards
- Buyers will place bids
- You'll receive WhatsApp notifications for each bid

### Checking Market Prices

```
Voice: "Naa, what is the price of shea butter today?"
```

ZAA will reply with current prices from different markets:
```
📊 Today's prices for shea butter:

• Tamale Central: ₵8/kg (A grade)
• Accra Makola: ₵12/kg (A grade)
• Export (FOB): ₵18/kg (A grade)

💡 Tip: Prices in Accra are typically 30-50% higher. Want me to help you sell directly to Accra buyers?
```

### Viewing Your Listings

```
Text: "Show my listings"
```

ZAA will show all your active listings with their current status.

### Group Selling (Optional)

```
Text: "Group selling for shea"
```

ZAA can coordinate with other farmers in your area to negotiate bulk prices.

---

## For Buyers: Using the Web Dashboard

### Accessing the Dashboard

1. **Open your browser** and go to `https://zaa.com/dashboard`
2. **Log in** with your buyer credentials
3. **Browse available listings** from farmers across Northern Ghana

### Finding Products

**Using Filters:**
- **Commodity**: Select shea butter, maize, groundnuts, etc.
- **Location**: Filter by region (Northern, Savannah, North East, etc.)
- **AI Grade**: Filter by quality (A=Premium, B=Standard, C=Economy)
- **Price Range**: Set minimum and maximum price per kg

**Understanding Listing Cards:**
- **Grade Badge**: AI-assigned quality (A/B/C)
- **AI Confidence**: How certain the AI is about the grading
- **Seller Rating**: Historical reputation of the seller
- **Market Comparison**: Asking price vs. local/regional/export prices
- **AI Analysis**: Detailed quality attributes (color, texture, moisture, etc.)

### Placing a Bid

1. **Click "Place Bid"** on a listing
2. **Enter your offer** in GHS per kg
3. **Review escrow information**
4. **Confirm bid**

The seller will receive a WhatsApp notification instantly.

### Managing Your Bids

- **Active Bids**: View all your pending bids
- **Negotiations**: Accept or counter offers via WhatsApp replies
- **Completed Transactions**: Track delivery and payment status

---

## Complete Transaction Flow

### Step 1: Farmer Lists via WhatsApp

**Farmer Action:**
```
Voice: "Naa, I have 50kg of shea butter. I want to sell."
```

**Backend Process:**
```
Voice note arrives at FastAPI server
    ↓
Whisper API → "Naa, I have 50kg of shea butter. I want to sell."
    ↓
Llama 3 AI → intent: "list_product"
              entities: {commodity: "shea butter", quantity: 50, unit: "kg"}
    ↓
Database → INSERT INTO listings (seller_id: Amina's ID, 
                                 commodity_id: shea_butter,
                                 quantity: 50, 
                                 unit: "kg",
                                 status: "active")
```

**Farmer Receives:**
```
✅ Great! I've listed your 50kg of shea butter.
Listing ID: #A3B7C9D2
Send me a photo and I'll grade the quality to help you get the best price.
```

### Step 2: Listing Appears on Buyer Dashboard

**Automatic Process:**
- The moment the listing is saved to the database, it instantly appears on the buyer dashboard
- No human approval needed
- No delay in listing availability

**Buyer Sees:**
```
┌─────────────────────────────────────────────────────────────┐
│  📸 [Photo placeholder]                                     │
│  Grade A  │  AI 92%                                        │
│                                                             │
│  Shea Butter — 50kg available                               │
│  Savelugu, Northern Region                                  │
│  Seller: Amina Y.  ★ 4.8                                    │
│                                                             │
│  💰 Asking: ₵10/kg    Market: ₵12/kg    Export: ₵18/kg     │
│                                                             │
│  AI Analysis:                                               │
│  • Color: ivory_white                                       │
│  • Texture: smooth                                          │
│  • Smell: nutty                                             │
│                                                             │
│  [Place Bid]                                                │
└─────────────────────────────────────────────────────────────┘
```

### Step 3: Farmer Gets Notified via WhatsApp

**Buyer Action:** Clicks "Place Bid" with offer of ₵11/kg

**Backend Process:**
```python
# In bid_service.py → place_bid() is called
# After saving the bid to the database:

await notify_seller_of_bid(bid)

# This function:
# 1. Looks up Amina's phone number from the database
# 2. Sends her a WhatsApp message (or voice note if she prefers Dagbani)
```

**Farmer Receives:**
```
🎉 New Bid Received!
Buyer: Global Shea Exports Ltd.
Offer: ₵11/kg
Total: ₵550
Quantity: 50kg

Reply ACCEPT A3B7C9 to accept this bid.
Reply COUNTER A3B7C9D2 12 to negotiate ₵12/kg.
Reply NO to reject.
```

### Step 4: Farmer Accepts via WhatsApp Reply

**Farmer Action:**
```
Text: "ACCEPT A3B7C9"
```

**Backend Process:**
```
Reply arrives
    ↓
Llama 3 AI → intent: "accept_bid"
              entities: {bid_id: "A3B7C9D2"}
    ↓
Database → UPDATE bids SET status = 'accepted'
           UPDATE listings SET status = 'negotiating'
           INSERT INTO transactions (status: 'pending', escrow: 'pending')
    ↓
Notification → Send WhatsApp to buyer:
    "🎉 Your bid was accepted! Please deposit ₵275 (50%) to escrow via MoMo."
    ↓
Notification → Send WhatsApp to farmer:
    "Deal confirmed! Buyer will deposit 50% soon. Prepare your shea butter for pickup."
```

### Step 5: Escrow & Delivery

**Process Flow:**
```
Buyer deposits ₵275 via MTN MoMo
    ↓
ZAA confirms payment → holds in escrow
    ↓
Amina receives WhatsApp: "Payment received! Please deliver to Tamale bus station."
    ↓
Amina delivers, buyer confirms receipt
    ↓
ZAA releases ₵539 to Amina (minus ₵11 platform fee)
    ↓
Amina receives MoMo alert: "You have ₵539 from ZAA"
```

---

## Notification System

### For Farmers (WhatsApp Notifications)

| Event | Message You Receive |
|-------|---------------------|
| Listing created | "Your listing is active. ID: #A3B7C9D2" |
| New bid received | "New bid: ₵11/kg. Reply ACCEPT or COUNTER" |
| Bid accepted | "Waiting for buyer payment..." |
| Payment received | "Payment confirmed! Prepare for delivery" |
| Delivery reminder | "Please deliver by Friday to [location]" |
| Delivery confirmed | "🎉 Buyer confirmed receipt. Payment released!" |
| Payment released | "You received ₵539 via MoMo" |
| Group target reached | "Your group reached 500kg! Negotiating bulk price..." |
| Price alert (weekly) | "Shea butter prices rose 15% this week" |

### For Buyers (Dashboard Notifications)

| Event | Dashboard Update |
|-------|------------------|
| New listing | Real-time appearance in listings grid |
| Bid status | Updates in "Your Bids" section |
| Payment pending | "Deposit 50% to escrow" prompt |
| Delivery tracking | Real-time status updates in transaction details |
| Transaction complete | Marked as completed in transaction history |

---

## Payment & Escrow Process

### How Escrow Protects Both Parties

**For Sellers:**
- Payment is held securely until delivery is confirmed
- No risk of delivering without payment
- Guaranteed payment for delivered goods

**For Buyers:**
- Payment is only released when goods are received
- Can inspect produce before final payment
- Protected against fraudulent sellers

### Escrow Timeline

1. **Bid Accepted**: Buyer deposits 50% of total value
2. **Payment Confirmed**: Funds held in ZAA escrow
3. **Delivery Arranged**: Both parties agree on delivery method
4. **Delivery Made**: Seller delivers produce
5. **Confirmation**: Buyer confirms receipt
6. **Final Payment**: Remaining 50% released to seller
7. **Platform Fee**: 2% fee deducted from total
8. **Final Settlement**: Seller receives net amount

### MTN MoMo Integration

- **Currency**: Ghana Cedis (GHS)
- **Payment Methods**: MTN Mobile Money
- **Instant Confirmation**: Real-time payment verification
- **Automatic Payout**: Automatic MoMo transfers upon transaction completion

---

## Dispute Resolution

### When Disputes Arise

**Common Dispute Types:**
- Quality disagreement
- Delivery delays
- Payment issues
- Communication problems

### Resolution Process

**Step 1: Initiate Dispute**
- Either party sends WhatsApp message: "DISPUTE [transaction ID]"
- Or buyer clicks "Report Issue" on dashboard

**Step 2: ZAA Investigation**
- ZAA reviews transaction history
- Examines evidence (photos, delivery confirmations)
- Contacts both parties via WhatsApp

**Step 3: Resolution Options**
- **Refund**: Escrow funds returned to buyer
- **Partial refund**: Adjusted amount based on actual delivery
- **Full release**: Funds released to seller if dispute resolved in their favor
- **Mediation**: ZAA facilitates negotiation between parties

**Step 4: Final Decision**
- ZAA makes final binding decision
- Funds are released according to resolution
- Transaction marked with dispute status for future reference

---

## The AI Photo Grading System

### How It Works

**When You Send a Photo:**
```
Amina sends photo via WhatsApp
    ↓
ZAA downloads the image
    ↓
AI Vision model analyzes:
  • Color (ivory white, cream, yellowish, grey)
  • Texture (smooth, grainy, crumbly)
  • Impurities (% visible foreign matter)
  • Moisture content (for grains)
  • Size estimate (for nuts)
    ↓
Database saves grading result
    ↓
Amina gets voice reply: "Grade A. Estimated value: ₵12/kg"
```

**Benefits:**
- **For Farmers**: Objective quality assessment helps you get fair prices
- **For Buyers**: Verified quality grades build trust in listings
- **For Both**: No need for physical inspection before transaction

### Quality Grades Explained

| Grade | Description | Typical Market Value |
|-------|-------------|---------------------|
| **A** | Premium quality, no visible defects | Highest market price |
| **B** | Standard quality, minor imperfections | Fair market price |
| **C** | Below standard, significant defects | Discounted price |

---

## Group Selling Feature

### What is Group Selling?

Multiple farmers in the same area combine their produce to negotiate bulk prices that are 25% higher than individual sales.

### How It Works

**Step 1: Join a Group**
```
Text: "Group selling for shea"
```

**Step 2: ZAA Coordinates**
- ZAA finds other farmers with similar commodities in your area
- Combines quantities when target (e.g., 500kg) is reached
- Negotiates bulk prices with large buyers

**Step 3: Group Benefits**
- **Higher prices**: Bulk premiums (typically 25% above individual)
- **Better access**: Connection to larger buyers and exporters
- **Collective bargaining**: More negotiating power as a group

**Step 4: Revenue Splitting**
- Each farmer receives payment based on their contribution percentage
- ZAA handles distribution automatically after group sale completion

---

## Frequently Asked Questions

### For Farmers

**Q: Do I need a smartphone?**
A: No, any phone with WhatsApp works, including basic feature phones.

**Q: Do I need to know how to read?**
A: No, you can use voice notes in your local language.

**Q: How do I get paid?**
A: Directly to your MTN MoMo wallet after delivery confirmation.

**Q: What if I don't have MoMo?**
A: Contact ZAA support to arrange alternative payment methods.

**Q: Can I list multiple products?**
A: Yes, you can have multiple active listings simultaneously.

**Q: How long does my listing stay active?**
A: 14 days by default, can be renewed.

### For Buyers

**Q: Is the AI grading accurate?**
A: The AI model is trained on thousands of produce samples and typically 85-92% accurate.

**Q: Can I negotiate prices?**
A: Yes, use the counter offer system via WhatsApp.

**Q: What if the seller doesn't deliver?**
A: Your escrow payment is fully refunded.

**Q: How do I arrange delivery?**
A: Coordinate with seller via WhatsApp; options include pickup, delivery, or neutral location.

**Q: Can I buy from multiple sellers?**
A: Yes, there's no limit on transactions.

### Technical Questions

**Q: Is my data safe?**
A: Yes, we use enterprise-grade security and comply with Ghana data protection laws.

**Q: What happens if WhatsApp is down?**
A: The system has SMS fallback for critical notifications.

**Q: Can I cancel a bid?**
A: Yes, until the seller accepts it.

**Q: How are prices determined?**
A: Market data is collected from local markets, regional hubs, and export prices.

---

## Support & Contact

### Getting Help

**WhatsApp Support:**
- Message ZAA: "HELP" or call our support line
- Response time: Within 24 hours

**Email Support:**
- support@zaa.com
- Response time: Within 48 hours

**Phone Support:**
- +233 55 123 4567 (during business hours)

### Emergency Issues

For urgent issues with:
- **Payment problems**: "PAYMENT HELP" in WhatsApp
- **Delivery disputes**: "DISPUTE [transaction ID]" in WhatsApp
- **System outages**: Check status.zaa.com

---

## Language Support

### Supported Languages

| Language | Code | Voice Support | Text Support |
|----------|------|---------------|---------------|
| Dagbani | dag | ✅ Full | ✅ Full |
| Twi | tw | ✅ Full | ✅ Full |
| Gonja | gon | ✅ Full | ✅ Limited |
| Hausa | ha | ✅ Full | ✅ Limited |
| English | en | ✅ Full | ✅ Full |

### Language Tips

- **Voice notes**: Speak clearly in your preferred language
- **Text messages**: Short sentences work best
- **Commodity names**: Use local names (e.g., "kpakpi" for shea nuts)
- **Numbers**: State quantities clearly (e.g., "fifty kilograms" vs "50kg")

---

## Security Best Practices

### For Farmers

- **Never share** your MoMo PIN with anyone
- **Verify** ZAA number before sharing sensitive info
- **Report** suspicious messages to ZAA support
- **Keep records** of your transactions

### For Buyers

- **Use strong passwords** for your dashboard account
- **Enable two-factor authentication** when available
- **Verify seller reputation** before placing large bids
- **Read terms** carefully before confirming transactions

---

## Glossary

- **AI**: Artificial Intelligence
- **Escrow**: Third-party holding of funds until conditions are met
- **Grade**: Quality rating (A=Premium, B=Standard, C=Economy)
- **Listing**: Product listing for sale
- **Bid**: Offer to purchase
- **MoMo**: Mobile Money (MTN's mobile payment service)
- **ZAA**: Meaning "tomorrow" in Dagbani

---

## Quick Reference Commands

### WhatsApp Commands for Farmers

| Command | Description |
|---------|-------------|
| "HELP" | Show available commands |
| "PRICES [commodity]" | Get current market prices |
| "SELL [commodity] [quantity]" | Create new listing |
| "LISTINGS" | View your active listings |
| "STATUS" | Check transaction status |
| "GROUP [commodity]" | Join group selling |
| "DISPUTE [ID]" | Report an issue |

### Dashboard Actions for Buyers

| Action | Description |
|--------|-------------|
| Browse listings | View all available produce |
| Apply filters | Narrow down by commodity, location, grade |
| Place bid | Make an offer on a listing |
| View bids | Track your active bids |
| Check transactions | Monitor purchase history |
| Report issue | Initiate dispute resolution |

---

*Last Updated: August 2026*
*Version: 1.0*
*For questions or support, contact: support@zaa.com*
