# AE Seller Discovery Tool

A comprehensive discovery questionnaire tool for Account Executives to capture all required information from new sellers during the onboarding process.

## 🔗 Live Tool
**go/ae-discovery-tool** → [https://kalanicuaresma.github.io/ae-discovery-tool](https://kalanicuaresma.github.io/ae-discovery-tool)

## Features

### 📋 9 Discovery Sections
1. **🏢 Business Overview** — Business name, locations, type, offering, revenue, employees
2. **⚠️ Goals & Pain Points** — Pain points, previous Square experience, inefficiencies, consolidation needs, decision makers
3. **🛠️ Migration Requirements** — Must-have/nice-to-have features, migration concerns, training needs
4. **🧰 Current POS & Tools** — Current POS, contract status, additional tools, checkout flow, kitchen setup
5. **💻 Technical Details** — Square product, SaaS tier, add-ons, pricing
6. **🔧 Hardware & Networking** — Networking assessment, cabling, site survey, per-location hardware config
7. **👥 Staffing & Configuration** — Roles/pay rates, tip distribution, scheduling, time clock
8. **📅 Timeline & Planning** — Go-live date, blackout dates, install window, GSO instructions
9. **📝 Notes & Special Instructions** — Internal notes, GSO attention items, competitive intel, risk factors, follow-ups

### 🔑 Key Capabilities
- **📊 Real-time Completion Tracking** — Per-section badges and overall % progress
- **☁️ Salesforce Integration** — Syncs discovery data to Salesforce opportunity fields
- **📤 Slack Automation** — Auto-generates Slack messages to #onboarding-handoffs when submitting
  - 🔴 **Incomplete** → Flags missing fields, notifies Onboarding Specialist to follow up
  - ✅ **Complete** → Full handoff summary with all key details
- **💾 Auto-Save** — Persists data in browser localStorage
- **📄 Example Data** — Pre-loads Triple Crossing Brewing example for training/demo

### 🎯 Why This Exists
Reverse-engineered from real discovery notes to ensure AEs consistently capture all critical information needed for a smooth seller onboarding handoff to GSO.

## Integration Setup

### Slack Webhook
1. Go to [api.slack.com/apps](https://api.slack.com/apps)
2. Create a new app or use existing
3. Enable Incoming Webhooks
4. Add webhook to `#onboarding-handoffs` channel
5. Copy the webhook URL and add it to the app configuration

### Salesforce Connected App
1. Salesforce Setup → App Manager → New Connected App
2. Enable OAuth, set callback URL to the hosted app URL
3. Add required scopes (API, refresh_token)
4. Copy Client ID and Secret to app configuration

## Development
This is a single-file HTML application with no build step required. Just open `index.html` in a browser.

## Deployment
Hosted via GitHub Pages. Any push to `main` auto-deploys.
