"""
evals/fixtures.py — Test cases for search eval.

Each fixture is a (brand_guidelines, niche) pair with expected behaviors:
what sources should appear, what topics are relevant, what should be avoided.

These are used for both heuristic checks (did the plan include site: queries?)
and LLM-as-judge evaluation (are the queries smart for this niche?).
"""

FIXTURES = [
    {
        "name": "aerie_music",
        "niche": "Music",
        "brand_guidelines": """# Brand Guidelines
## Brand Name
Aerie (by American Eagle Outfitters)
## Industry
Retail / Apparel & Intimates
## Tone of Voice
- Empathetic and unconditionally supportive
- Casual and peer-to-peer
- Authentic and transparent, matching the #AerieREAL ethos
## Target Audience
- Gen Z and Millennial women aged 15–35
- Individuals seeking everyday comfort
- Value-driven consumers who prioritize body inclusivity
## Key Messaging Pillars
1. #AerieREAL: Real power, real beauty, zero digital retouching
2. Effortless Comfort
3. Inclusivity First
## Topics to Avoid
- Weight loss, dieting, or "body transformation" narratives
- Airbrushing or digital modification
- High-fashion exclusivity
- Hyper-sexualized marketing
- Competitor bashing or body-shaming""",
        "expected_sources": ["billboard", "spotify", "tiktok", "youtube"],
        "expected_audience_keywords": ["gen z", "women", "15", "35", "millennial"],
        "bad_topics": ["weight loss", "dieting", "body transformation"],
    },
    {
        "name": "acme_ai",
        "niche": "AI and Tech",
        "brand_guidelines": """# Brand Guidelines
## Brand Name
Acme Tech Solutions
## Industry
Software / AI Tools
## Tone of Voice
- Confident but approachable
- Technically credible without being jargon-heavy
- Witty when appropriate, never sarcastic
## Target Audience
- Tech-savvy professionals aged 25-45
- Startup founders and product managers
- Developers exploring AI tools
## Key Messaging Pillars
1. We make AI practical, not theoretical
2. Built by developers, for developers
3. Ship faster without sacrificing quality
## Topics to Avoid
- Politics and political figures
- Religion
- Competitor bashing
- Unverified health/medical claims
- Anything involving ongoing lawsuits""",
        "expected_sources": ["hacker news", "techcrunch", "product hunt", "github", "the verge"],
        "expected_audience_keywords": ["developer", "startup", "professional", "25", "45", "tech"],
        "bad_topics": ["politics", "religion", "lawsuits"],
    },
    {
        "name": "aerie_fitness",
        "niche": "Fitness",
        "brand_guidelines": """# Brand Guidelines
## Brand Name
Aerie (by American Eagle Outfitters)
## Industry
Retail / Apparel & Intimates
## Tone of Voice
- Empathetic and unconditionally supportive
- Casual and peer-to-peer
## Target Audience
- Gen Z and Millennial women aged 15–35
- Individuals seeking everyday comfort
## Key Messaging Pillars
1. #AerieREAL
2. Effortless Comfort
3. Inclusivity First
## Topics to Avoid
- Weight loss, dieting, or "body transformation" narratives
- Body-shaming terminology""",
        "expected_sources": ["reddit", "strava", "nike", "women's health", "self"],
        "expected_audience_keywords": ["gen z", "women", "comfort", "inclusive"],
        "bad_topics": ["weight loss", "dieting", "body transformation", "body shaming"],
    },

    # --- Niche: Food & Beverage ---
    {
        "name": "chipotle_food",
        "niche": "Food and Dining",
        "brand_guidelines": """# Brand Guidelines
## Brand Name
Chipotle Mexican Grill
## Industry
Fast-Casual Restaurants
## Tone of Voice
- Witty, confident, and culturally plugged-in
- Casual and internet-native (meme-friendly)
- Transparent about ingredients and sourcing
## Target Audience
- Gen Z and Millennials aged 18–35
- Health-conscious but flavor-first consumers
- Urban and suburban young professionals and students
## Key Messaging Pillars
1. Real Ingredients: responsibly sourced, no artificial anything
2. Customization is king — your bowl, your way
3. Culturally relevant, always in the conversation
## Topics to Avoid
- Competitor bashing
- Food safety scares or illness references
- Political endorsements
- Animal cruelty imagery""",
        "expected_sources": ["tiktok", "eater", "bon appetit", "reddit", "food network"],
        "expected_audience_keywords": ["gen z", "millennial", "18", "35", "health"],
        "bad_topics": ["food safety", "illness", "animal cruelty"],
    },
    {
        "name": "oatly_food",
        "niche": "Food and Dining",
        "brand_guidelines": """# Brand Guidelines
## Brand Name
Oatly
## Industry
Plant-Based Food & Beverage
## Tone of Voice
- Irreverent and self-aware
- Anti-corporate corporate voice
- Playful, sometimes absurd, always honest
## Target Audience
- Environmentally conscious consumers aged 22–40
- Flexitarians and plant-curious (not just vegans)
- Urban professionals who care about sustainability
## Key Messaging Pillars
1. Post-milk generation — oat milk as a lifestyle
2. Transparency about environmental impact
3. Food should be fun, not preachy
## Topics to Avoid
- Shaming meat-eaters or dairy consumers
- Unsubstantiated health claims
- Political partisanship
- Greenwashing language""",
        "expected_sources": ["eater", "bon appetit", "reddit", "tiktok", "new york times"],
        "expected_audience_keywords": ["environment", "sustain", "plant", "urban", "22", "40"],
        "bad_topics": ["shaming", "greenwashing", "political"],
    },

    # --- Niche: Gaming ---
    {
        "name": "discord_gaming",
        "niche": "Gaming",
        "brand_guidelines": """# Brand Guidelines
## Brand Name
Discord
## Industry
Communication Platform / Gaming
## Tone of Voice
- Playful, warm, and community-first
- Gamer-native but welcoming to all communities
- Casual and emoji-friendly, never stiff
## Target Audience
- Gamers aged 16–30
- Online community builders and moderators
- Students and young professionals who live online
## Key Messaging Pillars
1. Your place to talk — gaming, studying, hanging out
2. Community is everything
3. Voice, video, text — however you connect
## Topics to Avoid
- Online harassment or toxicity framing
- Gambling or loot box promotion
- Violent extremism
- NSFW content""",
        "expected_sources": ["ign", "kotaku", "reddit", "twitch", "steam"],
        "expected_audience_keywords": ["gamer", "16", "30", "community", "student"],
        "bad_topics": ["harassment", "gambling", "extremism"],
    },
    {
        "name": "razer_gaming",
        "niche": "Gaming",
        "brand_guidelines": """# Brand Guidelines
## Brand Name
Razer
## Industry
Gaming Hardware & Peripherals
## Tone of Voice
- Bold, edgy, performance-driven
- Speaks to hardcore gamers as peers
- Tech-forward with competitive energy
## Target Audience
- Serious gamers aged 18–35
- Esports enthusiasts and competitive players
- Tech-savvy consumers who invest in premium gear
## Key Messaging Pillars
1. For Gamers. By Gamers.
2. Performance without compromise
3. Cutting-edge technology meets gaming culture
## Topics to Avoid
- Casual gaming dismissiveness
- Political controversies
- Health risks of gaming
- Competitor bashing""",
        "expected_sources": ["ign", "the verge", "reddit", "twitch", "steam"],
        "expected_audience_keywords": ["gamer", "esport", "18", "35", "competitive"],
        "bad_topics": ["health risks", "political", "competitor bashing"],
    },

    # --- Niche: Beauty & Skincare ---
    {
        "name": "glossier_beauty",
        "niche": "Beauty and Skincare",
        "brand_guidelines": """# Brand Guidelines
## Brand Name
Glossier
## Industry
Beauty & Skincare (DTC)
## Tone of Voice
- Best-friend energy — warm, approachable, real
- Skin-first, makeup-second philosophy
- Celebrates individuality over perfection
## Target Audience
- Women and non-binary individuals aged 18–32
- Skincare-curious consumers who prefer minimal routines
- Digitally native, Instagram and TikTok active
## Key Messaging Pillars
1. Skin first. Makeup second.
2. Beauty inspired by real life
3. Less is more — effortless, dewy, natural
## Topics to Avoid
- Heavy contouring or "Instagram face" promotion
- Anti-aging fear-mongering
- Unrealistic before/after transformations
- Animal testing""",
        "expected_sources": ["tiktok", "allure", "sephora", "reddit", "vogue"],
        "expected_audience_keywords": ["women", "18", "32", "skincare", "minimal"],
        "bad_topics": ["anti-aging fear", "animal testing", "unrealistic transformation"],
    },
    {
        "name": "ordinary_beauty",
        "niche": "Beauty and Skincare",
        "brand_guidelines": """# Brand Guidelines
## Brand Name
The Ordinary (by DECIEM)
## Industry
Clinical Skincare
## Tone of Voice
- Ingredient-first and educational
- No-nonsense, transparent pricing
- Science-backed without being intimidating
## Target Audience
- Skincare enthusiasts aged 20–40 who research ingredients
- Budget-conscious consumers seeking clinical results
- Reddit skincare community members (r/SkincareAddiction)
## Key Messaging Pillars
1. Clinical formulations. Honest pricing.
2. Know your ingredients
3. Effective skincare shouldn't cost a fortune
## Topics to Avoid
- Miracle cure claims
- Celebrity endorsements as proof of efficacy
- Luxury/exclusivity positioning
- Dermatological fear-mongering""",
        "expected_sources": ["reddit", "allure", "byrdie", "tiktok", "dermstore"],
        "expected_audience_keywords": ["skincare", "ingredient", "20", "40", "budget"],
        "bad_topics": ["miracle cure", "fear-mongering", "luxury"],
    },

    # --- Niche: Travel & Outdoors ---
    {
        "name": "rei_outdoors",
        "niche": "Travel and Outdoors",
        "brand_guidelines": """# Brand Guidelines
## Brand Name
REI Co-op
## Industry
Outdoor Retail / Co-operative
## Tone of Voice
- Passionate about the outdoors, never gatekeeping
- Inclusive and welcoming to all experience levels
- Purpose-driven — stewardship over salesmanship
## Target Audience
- Outdoor enthusiasts aged 25–50
- Hikers, campers, climbers, and trail runners
- Environmentally conscious consumers
## Key Messaging Pillars
1. A life outdoors is a life well lived
2. Stewardship of public lands and wild places
3. Co-op values: community over commerce
## Topics to Avoid
- Extreme risk glorification
- Environmental destruction imagery
- Political partisanship
- Luxury travel or resort culture""",
        "expected_sources": ["alltrails", "reddit", "outside magazine", "national geographic", "backpacker"],
        "expected_audience_keywords": ["outdoor", "hiker", "25", "50", "environment"],
        "bad_topics": ["extreme risk", "environmental destruction", "luxury resort"],
    },
    {
        "name": "airbnb_travel",
        "niche": "Travel and Outdoors",
        "brand_guidelines": """# Brand Guidelines
## Brand Name
Airbnb
## Industry
Travel & Hospitality Platform
## Tone of Voice
- Warm and human — stories over statistics
- Celebrates belonging and local experiences
- Aspirational but accessible
## Target Audience
- Travelers aged 22–45 seeking unique stays
- Experience-seekers over resort-seekers
- Remote workers and digital nomads
## Key Messaging Pillars
1. Belong Anywhere
2. Live like a local, not a tourist
3. Every home tells a story
## Topics to Avoid
- Housing crisis / gentrification debate
- Safety incidents or property damage
- Regulatory battles with cities
- Luxury hotel comparisons""",
        "expected_sources": ["tiktok", "condé nast traveler", "lonely planet", "reddit", "skyscanner"],
        "expected_audience_keywords": ["travel", "22", "45", "experience", "remote"],
        "bad_topics": ["housing crisis", "gentrification", "safety incidents"],
    },

    # --- Niche: Finance & Fintech ---
    {
        "name": "robinhood_finance",
        "niche": "Finance and Investing",
        "brand_guidelines": """# Brand Guidelines
## Brand Name
Robinhood
## Industry
Fintech / Investment Platform
## Tone of Voice
- Democratizing and empowering
- Simple, jargon-free financial language
- Optimistic about financial futures
## Target Audience
- First-time investors aged 20–35
- Gen Z and young Millennials entering the market
- People who learned about investing from social media
## Key Messaging Pillars
1. Investing for everyone — no minimums, no gatekeeping
2. Financial literacy through doing
3. Your money, your decisions
## Topics to Avoid
- Get-rich-quick promises
- Specific stock/crypto recommendations
- Meme stock glorification
- Regulatory controversies""",
        "expected_sources": ["reddit", "cnbc", "bloomberg", "tiktok", "yahoo finance"],
        "expected_audience_keywords": ["investor", "20", "35", "gen z", "financial"],
        "bad_topics": ["get-rich-quick", "meme stock", "regulatory"],
    },
    {
        "name": "stripe_finance",
        "niche": "Finance and Investing",
        "brand_guidelines": """# Brand Guidelines
## Brand Name
Stripe
## Industry
Payment Infrastructure / Fintech
## Tone of Voice
- Developer-first and technically precise
- Quietly confident — let the product speak
- Clear, concise, no fluff
## Target Audience
- Software developers and engineers aged 25–45
- Startup founders building payment flows
- Product managers at SaaS companies
## Key Messaging Pillars
1. The economic infrastructure for the internet
2. Increase the GDP of the internet
3. Build first, worry about payments later
## Topics to Avoid
- Financial advice or investment recommendations
- Political commentary
- Competitor bashing
- Crypto speculation""",
        "expected_sources": ["hacker news", "techcrunch", "github", "product hunt", "the verge"],
        "expected_audience_keywords": ["developer", "startup", "25", "45", "engineer"],
        "bad_topics": ["financial advice", "political", "crypto speculation"],
    },
]
