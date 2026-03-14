"""
Smaartbrand Auto - AI-Powered Chat Agent
Loads sentiment data dynamically from CSV files
"""

from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os
import json
import httpx
import csv
from pathlib import Path
from collections import defaultdict

app = FastAPI(title="Smaartbrand Auto API", description="DeciPro DECIDE Engine - AI Powered")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============== DYNAMIC DATA LOADING FROM CSVs ==============

def load_executive_dashboard(filepath: str) -> dict:
    """Load model-level sentiment scores from executive dashboard CSV"""
    models = {}
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                model = row['Model'].strip()
                
                # Convert sentiment scores to percentages (0-100 scale)
                # Original values are roughly -0.2 to +0.1, we normalize to 0-100
                safety_raw = float(row.get('Safety_Sentiment', 0) or 0)
                mileage_raw = float(row.get('Mileage_Sentiment', 0) or 0)
                tech_raw = float(row.get('Tech_Features_Sentiment', 0) or 0)
                
                # Normalize: -0.2 = 0%, 0 = 50%, +0.1 = 100%
                # Formula: (value + 0.2) / 0.3 * 100, clamped to 0-100
                def normalize(val):
                    score = int(((val + 0.15) / 0.25) * 100)
                    return max(0, min(100, score))
                
                models[model] = {
                    'name': model,
                    'safety_sentiment_raw': safety_raw,
                    'mileage_sentiment_raw': mileage_raw,
                    'tech_sentiment_raw': tech_raw,
                    'safety_score': normalize(safety_raw),
                    'mileage_score': normalize(mileage_raw),
                    'tech_score': normalize(tech_raw),
                    'emotion': row.get('Plutchik_Emotion', 'Neutral'),
                    'summary': row.get('One_Line_Summary', ''),
                }
                
                # Calculate overall score (weighted average)
                models[model]['overall_score'] = int(
                    models[model]['safety_score'] * 0.4 +
                    models[model]['mileage_score'] * 0.35 +
                    models[model]['tech_score'] * 0.25
                )
                
                # Assign brand based on model name
                maruti_models = ['Brezza', 'Ciaz', 'Dzire', 'Fronx', 'Grand Vitara', 'Jimny', 'Baleno', 'Swift', 'Ertiga']
                hyundai_models = ['Creta', 'Venue', 'Verna', 'Tucson', 'Alcazar', 'Exter', 'Aura']
                tata_models = ['Nexon', 'Punch', 'Harrier', 'Safari', 'Tigor', 'Curvv']
                honda_models = ['City', 'Amaze', 'Elevate']
                mahindra_models = ['Scorpio-N', 'Thar', 'XUV700', 'XUV300', 'XUV 3XO']
                
                if model in maruti_models:
                    models[model]['brand'] = 'Maruti'
                elif model in hyundai_models:
                    models[model]['brand'] = 'Hyundai'
                elif model in tata_models:
                    models[model]['brand'] = 'Tata'
                elif model in honda_models:
                    models[model]['brand'] = 'Honda'
                elif model in mahindra_models:
                    models[model]['brand'] = 'Mahindra'
                else:
                    models[model]['brand'] = 'Other'
                    
    except Exception as e:
        print(f"Error loading executive dashboard: {e}")
    
    return models


def load_detailed_insights(filepath: str) -> dict:
    """Load detailed comments and aggregate insights from detailed CSV"""
    model_comments = defaultdict(list)
    model_emotions = defaultdict(lambda: defaultdict(int))
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                model = row.get('Model', '').strip()
                if not model:
                    continue
                
                comment = row.get('Original_Comment', '') or row.get('Comment', '')
                emotion = row.get('Plutchik_Emotion', 'Neutral')
                summary = row.get('One_Line_Summary', '')
                
                safety = float(row.get('Safety_Sentiment', 0) or 0)
                mileage = float(row.get('Mileage_Sentiment', 0) or 0)
                tech = float(row.get('Tech_Features_Sentiment', 0) or 0)
                
                model_comments[model].append({
                    'comment': comment[:500] if comment else '',
                    'summary': summary,
                    'emotion': emotion,
                    'safety': safety,
                    'mileage': mileage,
                    'tech': tech
                })
                
                model_emotions[model][emotion] += 1
                
    except Exception as e:
        print(f"Error loading detailed insights: {e}")
    
    # Process into insights
    insights = {}
    for model, comments in model_comments.items():
        # Find dominant emotion
        emotions = model_emotions[model]
        dominant_emotion = max(emotions, key=emotions.get) if emotions else 'Neutral'
        
        # Get positive and negative comments
        positive = [c for c in comments if c['safety'] > 0 or c['mileage'] > 0 or c['tech'] > 0]
        negative = [c for c in comments if c['safety'] < 0 or c['mileage'] < 0 or c['tech'] < 0]
        
        insights[model] = {
            'total_comments': len(comments),
            'dominant_emotion': dominant_emotion,
            'emotion_breakdown': dict(emotions),
            'positive_count': len(positive),
            'negative_count': len(negative),
            'sample_positive': [c['summary'] for c in positive[:3] if c['summary']],
            'sample_negative': [c['summary'] for c in negative[:3] if c['summary']],
        }
    
    return insights


def build_sentiment_data():
    """Build complete sentiment data from CSV files"""
    
    data_dir = Path(__file__).parent / 'data'
    
    # Load from CSVs
    exec_path = data_dir / 'maruti_executive_dashboard.csv'
    detail_path = data_dir / 'maruti_detailed_insights.csv'
    
    models = {}
    insights = {}
    
    if exec_path.exists():
        models = load_executive_dashboard(str(exec_path))
        print(f"✅ Loaded {len(models)} models from executive dashboard")
    else:
        print(f"⚠️ Executive dashboard CSV not found at {exec_path}")
    
    if detail_path.exists():
        insights = load_detailed_insights(str(detail_path))
        print(f"✅ Loaded insights for {len(insights)} models from detailed CSV")
    else:
        print(f"⚠️ Detailed insights CSV not found at {detail_path}")
    
    # Merge insights into models
    for model, model_data in models.items():
        if model in insights:
            model_data['insights'] = insights[model]
    
    # Calculate brand summaries
    brand_scores = defaultdict(lambda: {'safety': [], 'mileage': [], 'tech': []})
    for model, data in models.items():
        brand = data.get('brand', 'Other')
        brand_scores[brand]['safety'].append(data['safety_score'])
        brand_scores[brand]['mileage'].append(data['mileage_score'])
        brand_scores[brand]['tech'].append(data['tech_score'])
    
    brand_summary = {}
    for brand, scores in brand_scores.items():
        brand_summary[brand] = {
            'safety': int(sum(scores['safety']) / len(scores['safety'])) if scores['safety'] else 0,
            'mileage': int(sum(scores['mileage']) / len(scores['mileage'])) if scores['mileage'] else 0,
            'tech': int(sum(scores['tech']) / len(scores['tech'])) if scores['tech'] else 0,
        }
    
    # Find leaders and opportunities
    sorted_by_safety = sorted(models.items(), key=lambda x: x[1]['safety_score'], reverse=True)
    sorted_by_mileage = sorted(models.items(), key=lambda x: x[1]['mileage_score'], reverse=True)
    sorted_by_overall = sorted(models.items(), key=lambda x: x[1]['overall_score'], reverse=True)
    
    # Identify conquest opportunities (competitor weaknesses)
    opportunities = []
    for model, data in models.items():
        if data['brand'] != 'Maruti':
            if data['safety_score'] < 40:
                opportunities.append({
                    'target': f"{model} Owners/Considerers",
                    'weakness': 'Safety',
                    'score': data['safety_score'],
                    'action': f"Target with Maruti safety messaging",
                    'priority': 'HIGH' if data['safety_score'] < 25 else 'MEDIUM'
                })
            if data['mileage_score'] < 40:
                opportunities.append({
                    'target': f"{model} Owners",
                    'weakness': 'Mileage',
                    'score': data['mileage_score'],
                    'action': f"Target with efficiency/hybrid messaging",
                    'priority': 'HIGH' if data['mileage_score'] < 25 else 'MEDIUM'
                })
    
    # Sort opportunities by priority
    opportunities.sort(key=lambda x: (0 if x['priority'] == 'HIGH' else 1, x['score']))
    
    return {
        'metadata': {
            'source': 'Reddit r/CarsIndia',
            'total_models': len(models),
            'data_files': ['maruti_executive_dashboard.csv', 'maruti_detailed_insights.csv'],
            'last_loaded': 'dynamic'
        },
        'models': models,
        'brand_summary': brand_summary,
        'leaders': {
            'safety': {'model': sorted_by_safety[0][0], 'score': sorted_by_safety[0][1]['safety_score']} if sorted_by_safety else {},
            'mileage': {'model': sorted_by_mileage[0][0], 'score': sorted_by_mileage[0][1]['mileage_score']} if sorted_by_mileage else {},
            'overall': {'model': sorted_by_overall[0][0], 'score': sorted_by_overall[0][1]['overall_score']} if sorted_by_overall else {},
        },
        'conquest_opportunities': opportunities[:5],
    }


# Load data on startup
print("🚗 Loading sentiment data from CSVs...")
SENTIMENT_DATA = build_sentiment_data()
print(f"✅ Data loaded: {len(SENTIMENT_DATA['models'])} models")


# ============== CLAUDE API ==============

SYSTEM_PROMPT = """You are an AI analyst for Smaartbrand Auto (Acquink), powered by the DeciPro DECIDE engine.
You analyze Reddit sentiment data to provide actionable insights for Maruti Suzuki executives.

FORMATTING RULES:
- Structure responses with 📊 INSIGHTS and 🎯 ACTIONS sections
- Actions must specify department: [Product], [Marketing], [Service], or [Sales]
- Include specific numbers/percentages from the data
- Be direct and actionable - executives need decisions
- Highlight Maruti advantages when comparing to competitors

SENTIMENT DATA (loaded from CSV files):
{data}

Key metrics explanation:
- Scores are 0-100 where higher is better
- safety_score: Positive sentiment about safety/build quality
- mileage_score: Positive sentiment about fuel efficiency
- tech_score: Positive sentiment about features/technology
- overall_score: Weighted composite (40% safety, 35% mileage, 25% tech)

When answering:
1. Reference specific scores (e.g., "Grand Vitara's 77% safety vs Creta's 22%")
2. Quote actual data from the CSVs
3. Provide department-specific actions [Product] [Marketing] [Sales] [Service]
4. Prioritize by business impact (HIGH/MEDIUM/LOW)"""


class ChatQuery(BaseModel):
    query: str


async def call_claude_api(query: str, api_key: str) -> str:
    """Call Claude API with sentiment data context"""
    
    system = SYSTEM_PROMPT.format(data=json.dumps(SENTIMENT_DATA, indent=2, default=str))
    
    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.post(
            "https://api.anthropic.com/v1/messages",
            headers={
                "Content-Type": "application/json",
                "x-api-key": api_key,
                "anthropic-version": "2023-06-01"
            },
            json={
                "model": "claude-sonnet-4-20250514",
                "max_tokens": 1500,
                "system": system,
                "messages": [{"role": "user", "content": query}]
            }
        )
        
        if response.status_code != 200:
            raise Exception(f"Claude API error: {response.status_code} - {response.text[:200]}")
        
        return response.json()["content"][0]["text"]


def fallback_response(query: str) -> str:
    """Rule-based fallback when no API key"""
    
    q = query.lower()
    models = SENTIMENT_DATA.get('models', {})
    
    # Model-specific responses
    for model_name, data in models.items():
        if model_name.lower() in q:
            r = f"📊 **{model_name} Analysis** (from CSV data)\n\n"
            r += f"**Brand:** {data.get('brand', 'Unknown')}\n"
            r += f"**Emotion:** {data.get('emotion', 'Neutral')}\n\n"
            r += f"**Sentiment Scores:**\n"
            r += f"• Safety: {data.get('safety_score', 0)}%\n"
            r += f"• Mileage: {data.get('mileage_score', 0)}%\n"
            r += f"• Tech: {data.get('tech_score', 0)}%\n"
            r += f"• Overall: {data.get('overall_score', 0)}%\n\n"
            
            if data.get('insights'):
                ins = data['insights']
                r += f"**Comments Analyzed:** {ins.get('total_comments', 0)}\n"
                r += f"**Dominant Emotion:** {ins.get('dominant_emotion', 'Neutral')}\n"
            
            r += f"\n**Summary:** {data.get('summary', 'No summary available')}\n"
            
            # Actions
            r += "\n🎯 **RECOMMENDED ACTIONS**\n"
            if data.get('brand') == 'Maruti':
                if data.get('safety_score', 0) > 60:
                    r += f"[Marketing] Lead with {model_name}'s safety advantage\n"
                if data.get('mileage_score', 0) > 60:
                    r += f"[Marketing] Promote efficiency leadership\n"
            else:
                r += f"[Marketing] Target {model_name} considerers with Maruti safety/efficiency messaging\n"
                r += f"[Sales] Train staff on {model_name}'s weaknesses\n"
            
            return r
    
    # Safety query
    if "safety" in q:
        sorted_models = sorted(models.items(), key=lambda x: x[1].get('safety_score', 0), reverse=True)
        r = "📊 **Safety Sentiment Analysis** (from CSV)\n\n"
        r += "**Top 5 (Safety Score):**\n"
        for model, data in sorted_models[:5]:
            r += f"• {model}: {data.get('safety_score', 0)}% ({data.get('brand', '')})\n"
        r += "\n**Bottom 5:**\n"
        for model, data in sorted_models[-5:]:
            r += f"• {model}: {data.get('safety_score', 0)}% ({data.get('brand', '')})\n"
        return r
    
    # Mileage query
    if "mileage" in q or "efficiency" in q or "fuel" in q:
        sorted_models = sorted(models.items(), key=lambda x: x[1].get('mileage_score', 0), reverse=True)
        r = "📊 **Mileage/Efficiency Analysis** (from CSV)\n\n"
        r += "**Top 5:**\n"
        for model, data in sorted_models[:5]:
            r += f"• {model}: {data.get('mileage_score', 0)}% ({data.get('brand', '')})\n"
        r += "\n**Bottom 5:**\n"
        for model, data in sorted_models[-5:]:
            r += f"• {model}: {data.get('mileage_score', 0)}% ({data.get('brand', '')})\n"
        return r
    
    # Opportunities
    if "opportunity" in q or "conquest" in q:
        r = "📊 **Conquest Opportunities** (from CSV)\n\n"
        for opp in SENTIMENT_DATA.get('conquest_opportunities', [])[:5]:
            r += f"**{opp['target']}** [{opp['priority']}]\n"
            r += f"• Weakness: {opp['weakness']} ({opp['score']}%)\n"
            r += f"• Action: {opp['action']}\n\n"
        return r
    
    # Default
    return f"""👋 **Smaartbrand Auto AI**

Data loaded from CSV files: **{len(models)} models**

**Try asking:**
• "Tell me about Grand Vitara"
• "Analyze Creta"
• "Safety sentiment analysis"
• "Mileage comparison"
• "Conquest opportunities"

💡 Add `ANTHROPIC_API_KEY` in Railway for full AI responses."""


# ============== API ENDPOINTS ==============

@app.get("/")
async def root():
    return FileResponse("frontend/index.html")


@app.get("/api/health")
async def health():
    has_key = bool(os.environ.get("ANTHROPIC_API_KEY"))
    return {
        "status": "healthy",
        "ai_enabled": has_key,
        "models_loaded": len(SENTIMENT_DATA.get('models', {})),
        "data_source": "CSV files (dynamic)"
    }


@app.post("/api/chat")
async def chat(query: ChatQuery):
    """Chat endpoint - uses Claude if API key configured"""
    
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    
    try:
        if api_key:
            response_text = await call_claude_api(query.query, api_key)
            return {"response": response_text, "ai_powered": True, "model": "claude-sonnet-4-20250514"}
        else:
            response_text = fallback_response(query.query)
            return {"response": response_text, "ai_powered": False, "model": "rule-based"}
    except Exception as e:
        print(f"API Error: {e}")
        response_text = fallback_response(query.query)
        return {"response": response_text, "ai_powered": False, "error": str(e)[:100]}


@app.get("/api/data")
async def get_data():
    """Return all loaded sentiment data"""
    return SENTIMENT_DATA


@app.get("/api/models")
async def get_models():
    """Get all model data"""
    return SENTIMENT_DATA.get('models', {})


@app.get("/api/models/{model_name}")
async def get_model(model_name: str):
    """Get specific model data"""
    models = SENTIMENT_DATA.get('models', {})
    
    # Try exact match first
    if model_name in models:
        return models[model_name]
    
    # Try case-insensitive
    for name, data in models.items():
        if name.lower() == model_name.lower():
            return data
    
    raise HTTPException(status_code=404, detail=f"Model '{model_name}' not found")


@app.get("/api/executive-summary")
async def executive_summary():
    """Get executive dashboard data"""
    return {
        "metadata": SENTIMENT_DATA.get('metadata', {}),
        "leaders": SENTIMENT_DATA.get('leaders', {}),
        "brand_summary": SENTIMENT_DATA.get('brand_summary', {}),
        "conquest_opportunities": SENTIMENT_DATA.get('conquest_opportunities', []),
    }


@app.post("/api/reload")
async def reload_data():
    """Reload data from CSV files (useful after updating CSVs)"""
    global SENTIMENT_DATA
    SENTIMENT_DATA = build_sentiment_data()
    return {"status": "reloaded", "models": len(SENTIMENT_DATA.get('models', {}))}


# Mount static files
app.mount("/static", StaticFiles(directory="frontend"), name="static")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 8000)))
