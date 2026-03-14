# Smaartbrand Auto Intelligence

**DeciPro DECIDE Engine - AI-Powered Automotive Sentiment Analysis**

Built by Acquink for Maruti Suzuki

## 📊 Data Source

The app loads sentiment data **dynamically from CSV files** in the `/data` folder:

| File | Contents |
|------|----------|
| `maruti_executive_dashboard.csv` | Model-level sentiment scores |
| `maruti_detailed_insights.csv` | Individual comments with sentiment |

### To Update Data:

1. Replace CSV files in the `/data` folder
2. Redeploy on Railway, OR
3. Call `POST /api/reload` to reload without redeploying

CSV columns expected:
- `Model` - Car model name
- `Safety_Sentiment` - Raw sentiment score (-0.2 to +0.1)
- `Mileage_Sentiment` - Raw sentiment score
- `Tech_Features_Sentiment` - Raw sentiment score
- `Plutchik_Emotion` - Dominant emotion
- `One_Line_Summary` - Brief summary

## 🤖 AI Configuration

The chat agent supports **real Claude AI** or falls back to rule-based responses:

| Mode | Status | How to Enable |
|------|--------|---------------|
| **Claude AI** | Recommended | Add `ANTHROPIC_API_KEY` env var |
| **Rule-based** | Default | No API key needed |

### Enable Claude AI on Railway:

1. Go to your Railway project
2. Click **Variables** tab
3. Add: `ANTHROPIC_API_KEY` = `sk-ant-api03-xxxxx`
4. Redeploy

The app will automatically detect the API key and use Claude Sonnet for responses.

## 🚀 Deploy to Railway

### Option 1: One-Click Deploy
[![Deploy on Railway](https://railway.app/button.svg)](https://railway.app/new)

### Option 2: Manual Deploy

1. **Create Railway Account**
   - Go to [railway.app](https://railway.app)
   - Sign up with GitHub

2. **Create New Project**
   ```bash
   # Install Railway CLI
   npm install -g @railway/cli
   
   # Login
   railway login
   
   # Create new project
   railway init
   ```

3. **Deploy**
   ```bash
   # From this directory
   railway up
   ```

4. **Get Your URL**
   ```bash
   railway open
   ```

## 📁 Project Structure

```
smaartbrand-railway/
├── main.py              # FastAPI backend with AI chat engine
├── requirements.txt     # Python dependencies
├── Procfile            # Railway process file
├── railway.json        # Railway config
├── nixpacks.toml       # Build config
└── frontend/
    └── index.html      # React frontend (self-contained)
```

## 🎯 Features

### Dashboard
- Executive KPIs: Overall Maruti Score, Safety Leader, Efficiency Leader
- Model Ranking by Overall Satisfaction
- Brand Associations Heatmap (Safety, Mileage, Tech)
- Strategic Insights Summary

### Chat Agent
Ask questions like:
- "How do I beat Creta?"
- "What's hurting Grand Vitara?"
- "Tell me about safety sentiment"
- "Show me conquest opportunities"
- "Compare Maruti vs Hyundai"

Each response includes:
- 📊 **Insights** with sentiment scores
- 🎯 **Actions by Department** (Product, Marketing, Service, Sales)
- **Emotional Signatures** (Joy, Trust, Fear, Anger)

## 🔌 API Endpoints

| Endpoint | Description |
|----------|-------------|
| `GET /` | Frontend dashboard |
| `GET /api/health` | Health check |
| `POST /api/chat` | Chat query endpoint |
| `GET /api/models` | All model data |
| `GET /api/models/{name}` | Specific model |
| `GET /api/aspects` | All aspect analysis |
| `GET /api/executive-summary` | Dashboard KPIs |

## 📊 Data Source 

- **Reddit r/CarsIndia**: 5,000 verified owner reviews
- **Analysis Period**: 24 months
- **Models Covered**: 15 models across 5 brands
- **Aspects**: Safety, Mileage, Tech/Features

## 🏆 Key Findings

| Insight | Maruti Action |
|---------|---------------|
| Grand Vitara 96% vs Creta 14% safety | Lead with crash test messaging |
| Honda City 3% mileage score | Target with Ciaz Hybrid |
| Tech gap neutralized | Focus on cabin quality next |
| Fronx 88% efficiency leader | "Mileage Champion" campaign |

---



Built with ❤️ by Acquink | Powered by DeciPro DECIDE Engine
