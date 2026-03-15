"""
Smaartbrand Auto - AI-Powered Decision Intelligence for Automotive
DeciPro DECIDE Engine - Maruti Suzuki POC
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


# ============== ENHANCED SYSTEM PROMPT ==============

SYSTEM_PROMPT = """You are SmaartAuto, an automotive decision intelligence assistant powered by DeciPro DECIDE Engine.

=== WHO YOU SERVE ===
Automotive brand teams who need actionable intelligence:
- Brand Manager - Brand perception, competitive positioning, conquest opportunities
- Marketing Head - Campaign messaging, USPs, competitor weaknesses to exploit
- Product Planning - Feature gaps, what to build next, segment opportunities
- Sales Training - Competitor talk tracks, objection handling, win themes
- Service & After-Sales - Ownership experience, service network perception
- R&D / Engineering - Technical feedback, quality issues, feature requests

=== YOUR DATA SOURCE ===
5,000 verified owner reviews from Reddit r/CarsIndia (24 months)
Analyzed using Acquink Multiple Aspect Sentiment Insights
Covers 27 car models across 5 brands (Maruti, Hyundai, Tata, Honda, Mahindra)
Equivalent to 100 traditional focus groups | Margin of error <1.5%

=== SAFETY SENTIMENT RANKING (0-100%) ===
| Rank | Model        | Score | Brand    | Insight |
|------|--------------|-------|----------|---------|
| 1    | Grand Vitara | 96%   | Maruti   | "Solid build", "tank-like", GNCAP praise |
| 2    | Brezza       | 88%   | Maruti   | Strong platform perception |
| 3    | Nexon        | 85%   | Tata     | 5-star rating mentioned often |
| 4    | Creta        | 14%   | Hyundai  | ⚠️ CRITICAL - "tin can", "unstable shell" |
| 5    | Scorpio-N    | 11%   | Mahindra | Safety concerns despite size |
| 6    | Thar         | 7%    | Mahindra | Lowest - rollover fears |

=== MILEAGE/EFFICIENCY SENTIMENT (0-100%) ===
| Rank | Model        | Score | Brand    | Insight |
|------|--------------|-------|----------|---------|
| 1    | Fronx        | 88%   | Maruti   | Segment leader, hybrid praised |
| 2    | Grand Vitara | 85%   | Maruti   | Strong hybrid delivers 20+ kmpl |
| 3    | Creta        | 81%   | Hyundai  | Acceptable efficiency |
| 4    | Ciaz         | 62%   | Maruti   | Good but dated perception |
| 5    | Verna        | 37%   | Hyundai  | Below expectations |
| 6    | City         | 3%    | Honda    | ⚠️ CRITICAL - "thirsty", "single digit mileage" anger |

=== TECH/FEATURES SENTIMENT (0-100%) ===
| Rank | Model        | Score | Brand    | Insight |
|------|--------------|-------|----------|---------|
| 1    | Grand Vitara | 85%   | Maruti   | HUD, 360 camera, ADAS praised |
| 2    | Creta        | 81%   | Hyundai  | Feature-loaded perception |
| 3    | Nexon        | 57%   | Tata     | Good but UI complaints |
| 4    | Elevate      | 3%    | Honda    | ⚠️ CRITICAL - "outdated infotainment" |

=== OVERALL ENGINEERING SATISFACTION (Composite: 40% Safety + 35% Mileage + 25% Tech) ===
| Rank | Model      | Score | Brand    |
|------|------------|-------|----------|
| 1    | Grand Vitara | 92% | Maruti   |
| 2    | Nexon      | 88%   | Tata     |
| 3    | Brezza     | 81%   | Maruti   |
| 4    | Fronx      | 74%   | Maruti   |
| 5    | Venue      | 66%   | Hyundai  |
| 6    | Punch      | 55%   | Tata     |
| 7    | Creta      | 51%   | Hyundai  |
| 8    | City       | 48%   | Honda    |
| 9    | Verna      | 44%   | Hyundai  |
| 10   | Harrier    | 40%   | Tata     |
| 11   | XUV700     | 29%   | Mahindra |
| 12   | Ciaz       | 25%   | Maruti   |
| 13   | Elevate    | 22%   | Honda    |
| 14   | Scorpio-N  | 18%   | Mahindra |
| 15   | Thar       | 7%    | Mahindra |

=== BRAND HEATMAP (Relative Position 0-100) ===
| Brand    | Safety | Mileage | Tech | Key Insight |
|----------|--------|---------|------|-------------|
| Maruti   | 100    | 100     | 80   | LEADS Safety & Mileage |
| Hyundai  | 60     | 40      | 100  | LEADS Tech only (but gap neutralized) |
| Tata     | 40     | 80      | 20   | Safety improving, tech lagging |
| Honda    | 80     | 60      | 60   | Balanced but no leadership |
| Mahindra | 20     | 20      | 40   | Weakest overall perception |

=== SENTIMENT DNA (What Drives Each Model's Perception) ===
| Model        | Mileage% | Safety% | Tech% | Primary Driver |
|--------------|----------|---------|-------|----------------|
| Elevate      | 31%      | 69%     | 18%   | Safety focus |
| Harrier      | 29%      | 53%     | 18%   | Safety focus |
| City         | 50%      | 29%     | 24%   | Mileage complaints |
| Brezza       | 29%      | 46%     | 16%   | Safety praise |
| Ciaz         | 37%      | 46%     | 17%   | Balanced |
| Curvv        | 40%      | 43%     | 17%   | Balanced |
| Alcazar      | 26%      | 43%     | 31%   | Tech interest |
| Grand Vitara | 32%      | 42%     | 27%   | Balanced positive |
| Aura         | 26%      | 41%     | 33%   | Tech interest |
| Exter        | 19%      | 41%     | 41%   | Tech interest |
| Dzire        | 36%      | 40%     | 24%   | Mileage focus |
| Jimny        | 30%      | 36%     | 32%   | Balanced |
| Fronx        | 39%      | 29%     | 31%   | Mileage leader |
| Amaze        | 41%      | 28%     | 31%   | Mileage focus |
| Creta        | 40%      | 24%     | 36%   | Tech/Features focus |

=== TOP 5 SENTIMENT DRIVERS BY MODEL ===

**Hyundai Creta:**
- ✅ Positive: Features 20%, Resale Value 15%, Performance 12%, Panoramic Sunroof 10%, Look 8%
- ❌ Negative: Safety 18%, Build Quality 12%, Mileage 10%, Waiting Period 8%, Heating 5%

**Honda City:**
- ✅ Positive: Engine 15%, Rear Comfort 14%, Brand Image 10%, Handling 8%, Space 6%
- ❌ Negative: City Mileage 18%, Ground Clearance 12%, Infotainment 10%, Tyres 8%, Cabin Noise 5%

**Grand Vitara:**
- ✅ Positive: Hybrid Mileage 18%, Build Quality 12%, Looks 9%, Service Network 8%, Features 7%
- ❌ Negative: Boot Space 10%, Interior Plastic 8%, Price 6%, Waiting Period 5%, Sunroof 4%

=== EMOTIONAL SIGNATURES (Plutchik Analysis) ===
| Model        | Primary   | Secondary | Tertiary     | Insight |
|--------------|-----------|-----------|--------------|---------|
| Grand Vitara | Joy 😊    | Trust 💚  | Anticipation | Happy owners, brand loyalty |
| Creta        | Fear 😰   | Joy       | Anticipation | Safety anxiety dominates |
| City         | Anger 😠  | Fear      | Anticipation | Mileage frustration |
| Ciaz         | Fear      | Disgust 😤| Trust        | Mixed feelings |

=== GENDER INSIGHTS ===
- Male Commenters: ~78% of discussions
  - Priority: Safety (42%) > Mileage (35%) > Tech (23%)
  - More vocal about: Build quality, crash tests, driving dynamics
  
- Female Commenters: ~22% of discussions
  - Priority: Safety (45%) > Tech (30%) > Mileage (25%)
  - More vocal about: Service network (+12%), interior quality, ease of driving

=== BUYER PERSONA PATTERNS ===

**First-Time Buyers (Est. 30%):**
- Primary concern: Mileage/running costs, resale value, service cost
- Price sensitive, brand agnostic
- Target with: Efficiency messaging, cost of ownership

**Upgraders - Hatchback to SUV (Est. 35%):**
- Primary concern: Safety, features, brand image
- Willing to pay premium for perceived quality
- Target with: Safety ratings, premium positioning

**Family Buyers (Est. 25%):**
- Safety dominates 65% of their discussions
- Boot space, rear comfort important
- Target with: GNCAP ratings, family testimonials

**Enthusiasts (Est. 10%):**
- Performance, handling, driving dynamics
- Less price sensitive, brand loyal
- Target with: Driving experience, performance specs

=== SAFETY KEYWORDS (Most Spoken) ===
Build Quality, NCAP Rating, 5 Star, Solid, Stable, Tin Can, Crash Test, Shell, Heavy, Sturdy, Airbags, Body Roll, Thud Sound, Safe

=== TECH KEYWORDS (Most Spoken) ===
Sunroof, 360 Camera, ADAS, Touchscreen, Apple CarPlay, Android Auto, Digital Cluster, HUD, Ventilated Seats, Connected Car, Wireless Charging, Speakers, Navigation, UI/UX

=== MILEAGE KEYWORDS (Most Spoken) ===
City Mileage, Highway, KMPL, Hybrid, Petrol, Diesel, Traffic, Running Cost, Tank, Efficiency, Smart Hybrid, Single Digit, AC On, Performance, Economy

=== RESPONSE FORMAT (ALWAYS FOLLOW) ===

📊 **INSIGHT**: [2-3 sentences with specific % scores. Always compare to competitors.]

🎯 **ACTIONS BY DEPARTMENT**:

👔 **Brand Manager**: [Positioning action vs competitors]

📢 **Marketing**:
   ✓ PROMOTE: [Keywords/aspects where you WIN - use in ads]
   ✗ AVOID: [Keywords where competitor wins - don't mention]
   🎙️ Ad Hook: "[Actual owner phrase to use in campaigns]"
   🎯 Target Segment: [Who to target based on competitor weakness]

🏭 **Product Planning**: [Feature gap or build recommendation]

💼 **Sales Training**: [Talk track against specific competitor]

🔧 **Service/After-Sales**: [If service-related insights exist]

(Include 3-4 most relevant departments only)

=== COMPETITIVE INTELLIGENCE RULES ===
1. **WIN/LOSE Analysis**: "Grand Vitara Safety (96%) DESTROYS Creta (14%) - lead with this"
2. **Conquest Opportunities**: "City owners hate mileage (3%) - target with Ciaz Hybrid"
3. **Defensive Gaps**: "Nexon beats Brezza on overall (88% vs 81%) - address in marketing"
4. **Never recommend promoting aspects where competitor leads**

=== R&D MODE (New Car Planning) ===
When asked "what should I build?" or "new car focus":

🚗 **MARKET GAPS IDENTIFIED**:
1. [Gap 1 with data support]
2. [Gap 2 with data support]

📊 **SEGMENT ANALYSIS**:
- Underserved segments based on sentiment
- Competitor weaknesses to exploit

🛠️ **BUILD RECOMMENDATIONS**:
- Must-have features (based on positive sentiment drivers)
- Avoid features (negative ROI based on sentiment)
- Differentiation opportunities

👥 **TARGET PERSONA**: [Who would buy this based on patterns]

=== CONQUEST PLAYBOOK ===
When asked "How to beat [Competitor]":

⚔️ **BATTLE CARD: [Competitor Name]**

**Their Weaknesses (ATTACK HERE):**
- [Weakness 1 with %]
- [Weakness 2 with %]

**Their Strengths (AVOID/NEUTRALIZE):**
- [Strength 1 with %]

**Win Themes:**
- "[Exact messaging to use]"

**Target Audience:**
- [Who is unhappy with competitor]

=== LANGUAGE ===
If query is in Hindi, Tamil, Telugu, Kannada:
- Respond in SAME language
- Keep emoji headers

=== CRITICAL RULES ===
1. **USE EXACT STATS FROM ABOVE TABLES** - Do NOT recalculate or use different numbers.
   - Grand Vitara Safety = 96% (not 77%, not 80%)
   - Creta Safety = 14% (not 21%, not 20%)
   - Thar Safety = 7% (not 0%)
   - City Mileage = 3% (not 5%, not 10%)
2. Always cite specific % satisfaction scores from the tables above.
3. Be direct - automotive managers are busy.
4. Max 300 words.
5. ALWAYS end with 🎯 Actions by Department - UNLESS user asks for specs/specifications only.
6. When comparing, ALWAYS show both numbers (yours vs competitor).
7. Never hallucinate - use ONLY the exact percentages listed in the tables above.
8. **SPECS-ONLY QUERIES**: If user asks "compare specs", "specifications", "features comparison", or similar technical queries, respond with ONLY a clean specs table. NO sentiment analysis, NO action items, NO department recommendations. Just specs.
9. **"TELL ME ABOUT [CAR]" QUERIES**: Include a **📋 KEY SPECS** section 
   with price, engine, mileage, safety rating, and key features from 
   the VEHICLE SPECIFICATIONS data. Show specs BEFORE the action items.
=== REFERENCE DATA (for context, but use stats from tables above) ===
{data}

=== VEHICLE SPECIFICATIONS (Use for technical comparisons) ===
{specs}
"""


# ============== LOAD CAR SPECS ==============

def load_car_specs(filepath: str = "car_specs.json") -> dict:
    """Load vehicle specifications from JSON file"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        return {}
    except Exception as e:
        print(f"Error loading specs: {e}")
        return {}

CAR_SPECS = load_car_specs()


# ============== DYNAMIC DATA LOADING FROM CSVs ==============

def load_executive_dashboard(filepath: str) -> dict:
    """Load model-level sentiment scores from executive dashboard CSV"""
    models = {}
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                model = row['Model'].strip()
                
                safety_raw = float(row.get('Safety_Sentiment', 0) or 0)
                mileage_raw = float(row.get('Mileage_Sentiment', 0) or 0)
                tech_raw = float(row.get('Tech_Features_Sentiment', 0) or 0)
                
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
                
                models[model]['overall_score'] = int(
                    models[model]['safety_score'] * 0.4 +
                    models[model]['mileage_score'] * 0.35 +
                    models[model]['tech_score'] * 0.25
                )
                
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
    """Load detailed comments and aggregate insights including gender"""
    model_comments = defaultdict(list)
    model_emotions = defaultdict(lambda: defaultdict(int))
    model_gender = defaultdict(lambda: defaultdict(int))
    
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
                gender = row.get('Gender_Inferred', 'Unknown')
                
                safety = float(row.get('Safety_Sentiment', 0) or 0)
                mileage = float(row.get('Mileage_Sentiment', 0) or 0)
                tech = float(row.get('Tech_Features_Sentiment', 0) or 0)
                
                model_comments[model].append({
                    'comment': comment[:500] if comment else '',
                    'summary': summary,
                    'emotion': emotion,
                    'gender': gender,
                    'safety': safety,
                    'mileage': mileage,
                    'tech': tech
                })
                
                model_emotions[model][emotion] += 1
                model_gender[model][gender] += 1
                
    except Exception as e:
        print(f"Error loading detailed insights: {e}")
    
    insights = {}
    for model, comments in model_comments.items():
        emotions = model_emotions[model]
        dominant_emotion = max(emotions, key=emotions.get) if emotions else 'Neutral'
        
        # Gender breakdown
        genders = model_gender[model]
        total_gender = sum(genders.values())
        gender_pct = {g: round(c/total_gender*100) for g, c in genders.items()} if total_gender > 0 else {}
        
        positive = [c for c in comments if c['safety'] > 0 or c['mileage'] > 0 or c['tech'] > 0]
        negative = [c for c in comments if c['safety'] < 0 or c['mileage'] < 0 or c['tech'] < 0]
        
        insights[model] = {
            'total_comments': len(comments),
            'dominant_emotion': dominant_emotion,
            'emotion_breakdown': dict(emotions),
            'gender_breakdown': gender_pct,
            'positive_count': len(positive),
            'negative_count': len(negative),
            'sample_positive': [c['summary'] for c in positive[:3] if c['summary']],
            'sample_negative': [c['summary'] for c in negative[:3] if c['summary']],
        }
    
    return insights


def build_sentiment_data():
    """Build complete sentiment data from CSV files"""
    
    data_dir = Path(__file__).parent / 'data'
    
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
    
    for model, model_data in models.items():
        if model in insights:
            model_data['insights'] = insights[model]
    
    # Brand summaries
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
    
    # Leaders
    sorted_by_safety = sorted(models.items(), key=lambda x: x[1]['safety_score'], reverse=True)
    sorted_by_mileage = sorted(models.items(), key=lambda x: x[1]['mileage_score'], reverse=True)
    sorted_by_overall = sorted(models.items(), key=lambda x: x[1]['overall_score'], reverse=True)
    
    # Conquest opportunities
    opportunities = []
    for model, data in models.items():
        if data.get('brand') != 'Maruti':
            weaknesses = []
            if data['safety_score'] < 50:
                weaknesses.append(('Safety', data['safety_score']))
            if data['mileage_score'] < 50:
                weaknesses.append(('Mileage', data['mileage_score']))
            if data['tech_score'] < 50:
                weaknesses.append(('Tech', data['tech_score']))
            
            for aspect, score in weaknesses:
                opportunities.append({
                    'target': model,
                    'brand': data.get('brand'),
                    'weakness': aspect,
                    'score': score,
                    'priority': 'HIGH' if score < 30 else 'MEDIUM',
                    'action': f"Target {model} owners with Maruti's {aspect.lower()} advantage"
                })
    
    opportunities.sort(key=lambda x: x['score'])
    
    return {
        'models': models,
        'brand_summary': brand_summary,
        'leaders': {
            'safety': [(m, d['safety_score']) for m, d in sorted_by_safety[:5]],
            'mileage': [(m, d['mileage_score']) for m, d in sorted_by_mileage[:5]],
            'overall': [(m, d['overall_score']) for m, d in sorted_by_overall[:5]],
        },
        'conquest_opportunities': opportunities[:10],
        'metadata': {
            'total_models': len(models),
            'total_comments': sum(m.get('insights', {}).get('total_comments', 0) for m in models.values()),
            'source': 'Reddit r/CarsIndia',
            'period': '24 months',
        }
    }


# Load data on startup
print("🚗 Loading sentiment data from CSVs...")
SENTIMENT_DATA = build_sentiment_data()
print(f"✅ Data loaded: {len(SENTIMENT_DATA.get('models', {}))} models")


# ============== API MODELS ==============

class ChatQuery(BaseModel):
    query: str


# ============== CLAUDE API ==============

async def call_claude_api(query: str, api_key: str) -> str:
    """Call Claude API with enhanced automotive prompt"""
    
    specs_str = json.dumps(CAR_SPECS, indent=2, default=str) if CAR_SPECS else "{}"
    system = SYSTEM_PROMPT.format(
        data=json.dumps(SENTIMENT_DATA, indent=2, default=str),
        specs=specs_str
    )
    
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
    """Enhanced rule-based fallback when no API key"""
    
    q = query.lower()
    models = SENTIMENT_DATA.get('models', {})
    
    # New car / R&D query
    if any(x in q for x in ['new car', 'build', 'r&d', 'what should', 'focus', 'next car', 'planning']):
        r = """🚗 **NEW CAR PLANNING INTELLIGENCE**

📊 **MARKET GAPS IDENTIFIED:**

1. **Premium Compact SUV with 5-Star Safety**
   - Creta dominates but has 14% safety sentiment (CRITICAL weakness)
   - Grand Vitara proves safety sells (96% sentiment)
   - Gap: No sub-15L SUV with Maruti's safety + Hyundai's features

2. **Efficient Sedan Alternative to City**
   - Honda City has 3% mileage sentiment (owners HATE running costs)
   - Ciaz underperforming (25% overall) despite good efficiency
   - Gap: Modern sedan with hybrid tech + connected features

3. **Urban Crossover (Fronx successor)**
   - Fronx leads efficiency (88%) but trails on tech
   - Hyundai Venue winning younger buyers on features

🛠️ **BUILD RECOMMENDATIONS:**

**Must-Have (High ROI based on sentiment):**
- 5-Star GNCAP Safety (96% positive driver for Grand Vitara)
- Strong Hybrid powertrain (18% of positive Grand Vitara mentions)
- 360 Camera + HUD (neutralized Hyundai tech advantage)
- Solid build perception (owners say "thud sound", "heavy doors")

**Avoid (Low ROI):**
- Panoramic sunroof (10% mention but not purchase driver)
- Complex infotainment (10% negative for competitors)

👥 **TARGET PERSONA:**
- Upgraders from hatchback (35% of SUV considerers)
- Safety-conscious families (65% discussion weight)
- First-time car buyers seeking value + safety

🎯 **ACTIONS BY DEPARTMENT:**

👔 **Brand Manager**: Position as "Safe + Smart + Efficient" trinity

📢 **Marketing**: Lead with crash test ratings, real owner testimonials

🏭 **Product Planning**: Prioritize GNCAP prep over feature count

💼 **Sales Training**: "Safety costs nothing extra with Maruti"
"""
        return r
    
    # Beat competitor query
    for competitor in ['creta', 'city', 'nexon', 'venue', 'verna', 'harrier', 'xuv']:
        if competitor in q and ('beat' in q or 'against' in q or 'vs' in q or 'compete' in q):
            comp_data = None
            comp_name = competitor.title()
            for m, d in models.items():
                if competitor in m.lower():
                    comp_data = d
                    comp_name = m
                    break
            
            if comp_data:
                r = f"""⚔️ **BATTLE CARD: {comp_name}**

**Their Weaknesses (ATTACK HERE):**
"""
                if comp_data['safety_score'] < 50:
                    r += f"- 🛡️ Safety: {comp_data['safety_score']}% (CRITICAL - your Grand Vitara: 96%)\n"
                if comp_data['mileage_score'] < 50:
                    r += f"- ⛽ Mileage: {comp_data['mileage_score']}% (your Fronx: 88%)\n"
                if comp_data['tech_score'] < 50:
                    r += f"- 💻 Tech: {comp_data['tech_score']}%\n"
                
                r += f"\n**Their Strengths (NEUTRALIZE):**\n"
                if comp_data['safety_score'] >= 50:
                    r += f"- Safety: {comp_data['safety_score']}%\n"
                if comp_data['mileage_score'] >= 50:
                    r += f"- Mileage: {comp_data['mileage_score']}%\n"
                if comp_data['tech_score'] >= 50:
                    r += f"- Tech: {comp_data['tech_score']}%\n"
                
                r += f"""
**Emotional Profile:** {comp_data.get('emotion', 'Neutral')}

**Win Themes:**
- "Compare crash test ratings - we're 5-star, they're not"
- "Ask about REAL mileage from owners, not brochure claims"
- "Our service network: 4000+ touchpoints vs their {comp_data.get('brand', 'competitor')}"

**Target Audience:**
- {comp_name} considerers worried about safety
- Current {comp_name} owners unhappy with {['safety', 'mileage', 'tech'][0 if comp_data['safety_score'] < 50 else 1 if comp_data['mileage_score'] < 50 else 2]}

🎯 **ACTIONS:**

👔 **Brand Manager**: Comparative campaigns highlighting safety gap

📢 **Marketing**: 
   ✓ PROMOTE: "5-star safety", "crash test champion", "solid build"
   ✗ AVOID: {"features" if comp_data['tech_score'] > 70 else "nothing - attack on all fronts"}

💼 **Sales Training**: Show GNCAP videos, owner testimonials on build quality
"""
                return r
    
    # Model-specific responses
    for model_name, data in models.items():
        if model_name.lower() in q:
            ins = data.get('insights', {})
            gender = ins.get('gender_breakdown', {})
            
            r = f"""📊 **{model_name} ANALYSIS**

**Brand:** {data.get('brand', 'Unknown')}
**Overall Score:** {data.get('overall_score', 0)}%
**Dominant Emotion:** {data.get('emotion', 'Neutral')}

**Sentiment Breakdown:**
- 🛡️ Safety: {data.get('safety_score', 0)}%
- ⛽ Mileage: {data.get('mileage_score', 0)}%
- 💻 Tech: {data.get('tech_score', 0)}%

**Audience Profile:**
"""
            if gender:
                for g, pct in gender.items():
                    if pct > 5:
                        r += f"- {g}: {pct}%\n"
            
            r += f"""
**Comments Analyzed:** {ins.get('total_comments', 0)}
**Positive/Negative:** {ins.get('positive_count', 0)}/{ins.get('negative_count', 0)}

**Key Insight:** {data.get('summary', 'No summary available')}

🎯 **ACTIONS:**
"""
            if data.get('brand') == 'Maruti':
                if data.get('safety_score', 0) > 60:
                    r += f"\n👔 **Brand**: Lead with {model_name}'s safety leadership"
                if data.get('mileage_score', 0) > 60:
                    r += f"\n📢 **Marketing**: Promote efficiency - owners love it"
            else:
                r += f"\n👔 **Brand**: Target {model_name} considerers with Maruti alternatives"
                r += f"\n💼 **Sales**: Train on {model_name}'s weaknesses"
            
            return r
    
    # Safety query
    if "safety" in q:
        sorted_models = sorted(models.items(), key=lambda x: x[1].get('safety_score', 0), reverse=True)
        r = """📊 **SAFETY SENTIMENT ANALYSIS**

**🏆 LEADERS (Positive Safety Perception):**
"""
        for model, data in sorted_models[:5]:
            r += f"- {model}: {data.get('safety_score', 0)}% ({data.get('brand', '')})\n"
        
        r += "\n**⚠️ LAGGARDS (Safety Concerns):**\n"
        for model, data in sorted_models[-5:]:
            r += f"- {model}: {data.get('safety_score', 0)}% ({data.get('brand', '')})\n"
        
        r += """
🎯 **ACTIONS:**

👔 **Brand**: Maruti OWNS safety narrative - Grand Vitara (96%) vs Creta (14%)

📢 **Marketing**: 
   ✓ PROMOTE: "5-star safety", "GNCAP champion", "solid build"
   🎙️ Ad Hook: "Owners call it 'tank-like' and 'built like a vault'"

💼 **Sales**: Show crash test comparison videos during test drive
"""
        return r
    
    # Default
    return f"""👋 **Welcome to SmaartAuto AI**

I've analyzed **{len(models)} car models** from Reddit r/CarsIndia with **{SENTIMENT_DATA.get('metadata', {}).get('total_comments', 11500)}+ owner comments**.

**Try asking:**
• "How do I beat Creta?"
• "What should Maruti build next?"
• "Tell me about Grand Vitara"
• "Safety sentiment analysis"
• "Compare Brezza vs Venue"
• "Conquest opportunities"

💡 Add `ANTHROPIC_API_KEY` in Railway for full Claude AI responses.

🎯 **Quick Insight:** Grand Vitara (96% safety) DESTROYS Creta (14%) - this is your #1 conquest opportunity!
"""


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
    
    if model_name in models:
        return models[model_name]
    
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
    """Reload data from CSV files"""
    global SENTIMENT_DATA
    SENTIMENT_DATA = build_sentiment_data()
    return {"status": "reloaded", "models": len(SENTIMENT_DATA.get('models', {}))}


# Mount static files
import os as os_module
static_dir = "frontend"
if os_module.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 8000)))
