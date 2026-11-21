"""
tools/niche_registry.py — Niche source registry for search planning.

Maps each niche to its best trend sources, split by access method:

- crawlable: Google-indexed sites that work with site: queries
- closed: Platforms that block Google crawling — use "coverage about" queries
- aggregators: Proxy sites that surface data from closed platforms
- subreddits: Relevant Reddit communities (always crawlable)

The search planner injects the matching entry into its prompt so it
knows exactly which sources to target for each niche.
"""

NICHE_SOURCES = {
    "Music": {
        "crawlable": [
            {"domain": "billboard.com", "name": "Billboard", "what": "charts, rankings, industry news"},
            {"domain": "pitchfork.com", "name": "Pitchfork", "what": "reviews, new releases, features"},
            {"domain": "nme.com", "name": "NME", "what": "music news, festival coverage"},
            {"domain": "rollingstone.com", "name": "Rolling Stone", "what": "artist features, cultural trends"},
            {"domain": "stereogum.com", "name": "Stereogum", "what": "indie and alternative music trends"},
        ],
        "closed": [
            {"name": "Spotify", "coverage_query": '"spotify viral" OR "spotify top songs" OR "spotify charts"'},
            {"name": "TikTok", "coverage_query": '"trending on tiktok" sounds OR music OR viral'},
            {"name": "YouTube Music", "coverage_query": '"youtube music" trending OR "music video" viral'},
            {"name": "Apple Music", "coverage_query": '"apple music" top charts OR playlist'},
        ],
        "aggregators": [
            {"domain": "chartmetric.com", "name": "Chartmetric", "what": "cross-platform music analytics"},
            {"domain": "kworb.net", "name": "Kworb", "what": "Spotify and YouTube chart tracking"},
        ],
        "subreddits": ["r/music", "r/popheads", "r/hiphopheads", "r/indieheads"],
    },

    "AI and Tech": {
        "crawlable": [
            {"domain": "news.ycombinator.com", "name": "Hacker News", "what": "developer discussions, launches"},
            {"domain": "techcrunch.com", "name": "TechCrunch", "what": "startup news, funding, product launches"},
            {"domain": "theverge.com", "name": "The Verge", "what": "consumer tech, AI, gadgets"},
            {"domain": "arstechnica.com", "name": "Ars Technica", "what": "deep tech analysis"},
            {"domain": "producthunt.com", "name": "Product Hunt", "what": "new product launches, tools"},
            {"domain": "github.com", "name": "GitHub", "what": "trending repos, open source"},
            {"domain": "wired.com", "name": "Wired", "what": "tech culture, AI ethics, features"},
        ],
        "closed": [
            {"name": "Twitter/X tech", "coverage_query": '"tech twitter" OR "AI twitter" trending discussion'},
        ],
        "aggregators": [
            {"domain": "githubtrending.com", "name": "GitHub Trending", "what": "trending repositories"},
            {"domain": "hn.algolia.com", "name": "HN Search", "what": "top Hacker News discussions"},
        ],
        "subreddits": ["r/technology", "r/artificial", "r/MachineLearning", "r/programming"],
    },

    "Fitness": {
        "crawlable": [
            {"domain": "womenshealthmag.com", "name": "Women's Health", "what": "fitness trends, workouts, wellness"},
            {"domain": "menshealth.com", "name": "Men's Health", "what": "fitness, nutrition, training"},
            {"domain": "self.com", "name": "Self", "what": "wellness, workout trends, body positivity"},
            {"domain": "runnersworld.com", "name": "Runner's World", "what": "running trends, races, gear"},
            {"domain": "shape.com", "name": "Shape", "what": "fitness trends, healthy living"},
        ],
        "closed": [
            {"name": "Strava", "coverage_query": '"trending on strava" OR "strava challenge" OR "strava trends"'},
            {"name": "Nike Run Club", "coverage_query": '"nike run club" OR "nike training" trending challenge'},
            {"name": "TikTok fitness", "coverage_query": '"trending on tiktok" fitness OR workout OR gym'},
            {"name": "Instagram fitness", "coverage_query": '"fitness influencer" OR "gym trend" instagram reels'},
        ],
        "aggregators": [
            {"domain": "statista.com", "name": "Statista", "what": "fitness industry data and trends"},
        ],
        "subreddits": ["r/fitness", "r/xxfitness", "r/running", "r/bodyweightfitness"],
    },

    "Food and Dining": {
        "crawlable": [
            {"domain": "bonappetit.com", "name": "Bon Appetit", "what": "food trends, recipes, restaurant culture"},
            {"domain": "eater.com", "name": "Eater", "what": "restaurant news, food industry trends"},
            {"domain": "seriouseats.com", "name": "Serious Eats", "what": "food science, cooking techniques"},
            {"domain": "foodnetwork.com", "name": "Food Network", "what": "recipes, cooking shows, trends"},
            {"domain": "tastingtable.com", "name": "Tasting Table", "what": "food news, restaurant trends"},
            {"domain": "nytimes.com/section/food", "name": "NYT Food", "what": "food journalism, cultural trends"},
        ],
        "closed": [
            {"name": "TikTok food", "coverage_query": '"tiktok food trend" OR "viral recipe" OR "food tiktok"'},
            {"name": "Instagram food", "coverage_query": '"food instagram" OR "foodie trend" reels viral'},
        ],
        "aggregators": [
            {"domain": "trends.google.com", "name": "Google Trends", "what": "search interest for food terms"},
        ],
        "subreddits": ["r/cooking", "r/food", "r/foodhacks", "r/EatCheapAndHealthy"],
    },

    "Gaming": {
        "crawlable": [
            {"domain": "ign.com", "name": "IGN", "what": "game reviews, news, trailers"},
            {"domain": "kotaku.com", "name": "Kotaku", "what": "gaming culture, news, opinion"},
            {"domain": "gamespot.com", "name": "GameSpot", "what": "reviews, news, guides"},
            {"domain": "polygon.com", "name": "Polygon", "what": "gaming culture, features, news"},
            {"domain": "dexerto.com", "name": "Dexerto", "what": "esports, streaming, gaming news"},
            {"domain": "pcgamer.com", "name": "PC Gamer", "what": "PC gaming news, hardware, reviews"},
        ],
        "closed": [
            {"name": "Twitch", "coverage_query": '"trending on twitch" OR "twitch streamer" OR "top twitch games"'},
            {"name": "Steam", "coverage_query": '"steam top sellers" OR "steam trending" OR "most played steam"'},
            {"name": "YouTube Gaming", "coverage_query": '"youtube gaming" trending OR "gaming youtube" viral'},
            {"name": "Discord", "coverage_query": '"discord community" trending OR "discord server" popular gaming'},
        ],
        "aggregators": [
            {"domain": "steamdb.info", "name": "SteamDB", "what": "Steam player counts, sales, trends"},
            {"domain": "twitchtracker.com", "name": "TwitchTracker", "what": "Twitch viewership and streamer stats"},
            {"domain": "sullygnome.com", "name": "SullyGnome", "what": "Twitch analytics and trends"},
        ],
        "subreddits": ["r/gaming", "r/Games", "r/pcgaming", "r/esports"],
    },

    "Beauty and Skincare": {
        "crawlable": [
            {"domain": "allure.com", "name": "Allure", "what": "beauty trends, product reviews, skin science"},
            {"domain": "byrdie.com", "name": "Byrdie", "what": "skincare routines, beauty tips, trends"},
            {"domain": "vogue.com/beauty", "name": "Vogue Beauty", "what": "luxury beauty, trends, features"},
            {"domain": "refinery29.com", "name": "Refinery29", "what": "beauty culture, trends, reviews"},
            {"domain": "elle.com/beauty", "name": "Elle Beauty", "what": "beauty news, trends, tutorials"},
            {"domain": "cosmopolitan.com", "name": "Cosmopolitan", "what": "beauty trends, skincare advice"},
        ],
        "closed": [
            {"name": "TikTok beauty", "coverage_query": '"beauty tiktok" OR "skincare tiktok" viral trend'},
            {"name": "Instagram beauty", "coverage_query": '"beauty influencer" OR "skincare routine" instagram trending'},
            {"name": "Sephora", "coverage_query": '"sephora bestseller" OR "sephora trending" OR "sephora top products"'},
            {"name": "Dermstore", "coverage_query": '"dermstore" bestseller OR trending skincare'},
        ],
        "aggregators": [
            {"domain": "incidecoder.com", "name": "INCIDecoder", "what": "ingredient analysis and product trends"},
        ],
        "subreddits": ["r/SkincareAddiction", "r/MakeupAddiction", "r/AsianBeauty", "r/BeautyGuruChatter"],
    },

    "Travel and Outdoors": {
        "crawlable": [
            {"domain": "cntraveler.com", "name": "Conde Nast Traveler", "what": "destinations, travel trends"},
            {"domain": "lonelyplanet.com", "name": "Lonely Planet", "what": "travel guides, destination trends"},
            {"domain": "outsideonline.com", "name": "Outside", "what": "outdoor adventure, gear, conservation"},
            {"domain": "nationalgeographic.com", "name": "National Geographic", "what": "exploration, nature, conservation"},
            {"domain": "backpacker.com", "name": "Backpacker", "what": "hiking, trails, gear reviews"},
            {"domain": "afar.com", "name": "AFAR", "what": "experiential travel, cultural travel"},
        ],
        "closed": [
            {"name": "AllTrails", "coverage_query": '"alltrails" trending trails OR "most popular hikes" OR "alltrails top"'},
            {"name": "TikTok travel", "coverage_query": '"travel tiktok" OR "tiktok travel trend" viral destination'},
            {"name": "Skyscanner", "coverage_query": '"skyscanner" trending destinations OR "cheapest flights" OR "flight trends"'},
        ],
        "aggregators": [
            {"domain": "skyscanner.com/tips-and-inspiration", "name": "Skyscanner Trends", "what": "flight search trends"},
        ],
        "subreddits": ["r/travel", "r/backpacking", "r/CampingAndHiking", "r/digitalnomad"],
    },

    "Finance and Investing": {
        "crawlable": [
            {"domain": "cnbc.com", "name": "CNBC", "what": "market news, investing trends, economy"},
            {"domain": "bloomberg.com", "name": "Bloomberg", "what": "financial news, market data, analysis"},
            {"domain": "finance.yahoo.com", "name": "Yahoo Finance", "what": "stock data, market trends, news"},
            {"domain": "fool.com", "name": "Motley Fool", "what": "investing education, stock analysis"},
            {"domain": "nerdwallet.com", "name": "NerdWallet", "what": "personal finance, fintech reviews"},
            {"domain": "investopedia.com", "name": "Investopedia", "what": "financial education, market trends"},
        ],
        "closed": [
            {"name": "TikTok finance", "coverage_query": '"fintok" OR "finance tiktok" OR "investing tiktok" trending'},
            {"name": "Twitter/X finance", "coverage_query": '"fintwit" OR "finance twitter" trending stocks discussion'},
        ],
        "aggregators": [
            {"domain": "stockanalysis.com", "name": "Stock Analysis", "what": "market data, trending stocks"},
        ],
        "subreddits": ["r/wallstreetbets", "r/investing", "r/personalfinance", "r/stocks"],
    },

    "Fashion": {
        "crawlable": [
            {"domain": "vogue.com", "name": "Vogue", "what": "fashion trends, runway, designer news"},
            {"domain": "whowhatwear.com", "name": "Who What Wear", "what": "street style, affordable fashion"},
            {"domain": "highsnobiety.com", "name": "Highsnobiety", "what": "streetwear, sneakers, culture"},
            {"domain": "hypebeast.com", "name": "Hypebeast", "what": "streetwear, sneakers, drops"},
            {"domain": "elle.com/fashion", "name": "Elle Fashion", "what": "fashion news, trends, features"},
            {"domain": "gq.com", "name": "GQ", "what": "men's fashion, style trends"},
        ],
        "closed": [
            {"name": "TikTok fashion", "coverage_query": '"fashion tiktok" OR "outfit trend" OR "style tiktok" viral'},
            {"name": "Instagram fashion", "coverage_query": '"fashion influencer" OR "outfit inspo" instagram trending'},
            {"name": "Pinterest", "coverage_query": '"pinterest fashion trends" OR "pinterest style" trending'},
        ],
        "aggregators": [
            {"domain": "trendalytics.co", "name": "Trendalytics", "what": "consumer demand and fashion trend data"},
        ],
        "subreddits": ["r/streetwear", "r/malefashionadvice", "r/femalefashionadvice"],
    },
    "Education and Learning": {
        "crawlable": [
            {"domain": "edweek.org", "name": "Education Week", "what": "K-12 education news and policy"},
            {"domain": "edsurge.com", "name": "EdSurge", "what": "edtech news, product launches, trends"},
            {"domain": "chronicle.com", "name": "The Chronicle", "what": "higher education news and trends"},
            {"domain": "insidehighered.com", "name": "Inside Higher Ed", "what": "university news, admissions, policy"},
            {"domain": "classcentral.com", "name": "Class Central", "what": "online course rankings and reviews"},
        ],
        "closed": [
            {"name": "Coursera", "coverage_query": '"coursera" trending courses OR "most popular coursera" OR "coursera top"'},
            {"name": "TikTok education", "coverage_query": '"edutok" OR "studytok" OR "learn on tiktok" trending'},
            {"name": "YouTube education", "coverage_query": '"youtube education" trending OR "educational youtube" viral'},
        ],
        "aggregators": [
            {"domain": "classcentral.com/report", "name": "Class Central Reports", "what": "MOOC enrollment trends"},
        ],
        "subreddits": ["r/education", "r/Teachers", "r/edtech", "r/OnlineLearning"],
    },

    "Health and Wellness": {
        "crawlable": [
            {"domain": "webmd.com", "name": "WebMD", "what": "health news, conditions, treatments"},
            {"domain": "healthline.com", "name": "Healthline", "what": "health trends, nutrition, wellness"},
            {"domain": "everydayhealth.com", "name": "Everyday Health", "what": "wellness trends, health news"},
            {"domain": "mindbodygreen.com", "name": "MindBodyGreen", "what": "holistic wellness, nutrition, mindfulness"},
            {"domain": "well.blogs.nytimes.com", "name": "NYT Well", "what": "science-backed health journalism"},
        ],
        "closed": [
            {"name": "TikTok wellness", "coverage_query": '"wellness tiktok" OR "health tiktok" viral trend supplement'},
            {"name": "Instagram wellness", "coverage_query": '"wellness influencer" OR "health influencer" instagram trending'},
        ],
        "aggregators": [
            {"domain": "examine.com", "name": "Examine", "what": "supplement and nutrition research summaries"},
        ],
        "subreddits": ["r/health", "r/nutrition", "r/Supplements", "r/biohackers"],
    },

    "Parenting and Family": {
        "crawlable": [
            {"domain": "parents.com", "name": "Parents", "what": "parenting advice, product reviews, trends"},
            {"domain": "todaysparent.com", "name": "Today's Parent", "what": "family life, parenting news"},
            {"domain": "romper.com", "name": "Romper", "what": "modern parenting, pregnancy, kids"},
            {"domain": "scarymommy.com", "name": "Scary Mommy", "what": "relatable parenting culture, humor"},
            {"domain": "fatherly.com", "name": "Fatherly", "what": "dad-focused parenting, gear, advice"},
        ],
        "closed": [
            {"name": "TikTok parenting", "coverage_query": '"momtok" OR "parenting tiktok" OR "dadtok" trending viral'},
            {"name": "Instagram parenting", "coverage_query": '"parenting influencer" OR "mom influencer" instagram trending'},
        ],
        "aggregators": [],
        "subreddits": ["r/Parenting", "r/Mommit", "r/daddit", "r/beyondthebump"],
    },

    "Pets and Animals": {
        "crawlable": [
            {"domain": "akc.org", "name": "AKC", "what": "dog breeds, training, events"},
            {"domain": "petmd.com", "name": "PetMD", "what": "pet health, nutrition, care"},
            {"domain": "thedodo.com", "name": "The Dodo", "what": "animal stories, rescue, viral pets"},
            {"domain": "rover.com/blog", "name": "Rover Blog", "what": "pet care trends, breed popularity"},
            {"domain": "catster.com", "name": "Catster", "what": "cat care, breeds, behavior"},
        ],
        "closed": [
            {"name": "TikTok pets", "coverage_query": '"pet tiktok" OR "dog tiktok" OR "cat tiktok" viral trending'},
            {"name": "Instagram pets", "coverage_query": '"pet influencer" OR "dog instagram" OR "cat instagram" trending'},
        ],
        "aggregators": [],
        "subreddits": ["r/dogs", "r/cats", "r/pets", "r/aww"],
    },

    "Real Estate": {
        "crawlable": [
            {"domain": "zillow.com/research", "name": "Zillow Research", "what": "housing market data, forecasts"},
            {"domain": "realtor.com/research", "name": "Realtor Research", "what": "market trends, inventory data"},
            {"domain": "curbed.com", "name": "Curbed", "what": "housing, urban development, design"},
            {"domain": "biggerpockets.com", "name": "BiggerPockets", "what": "real estate investing, market analysis"},
            {"domain": "housingwire.com", "name": "HousingWire", "what": "mortgage, lending, housing industry news"},
        ],
        "closed": [
            {"name": "TikTok real estate", "coverage_query": '"real estate tiktok" OR "housetok" OR "realtortok" trending'},
            {"name": "Redfin data", "coverage_query": '"redfin" market data OR housing trends OR "redfin report"'},
        ],
        "aggregators": [
            {"domain": "fred.stlouisfed.org", "name": "FRED", "what": "Federal Reserve economic and housing data"},
        ],
        "subreddits": ["r/RealEstate", "r/realestateinvesting", "r/FirstTimeHomeBuyer", "r/REBubble"],
    },

    "Automotive": {
        "crawlable": [
            {"domain": "caranddriver.com", "name": "Car and Driver", "what": "car reviews, news, comparisons"},
            {"domain": "motortrend.com", "name": "MotorTrend", "what": "car reviews, industry news, shows"},
            {"domain": "thedrive.com", "name": "The Drive", "what": "automotive culture, news, tech"},
            {"domain": "electrek.co", "name": "Electrek", "what": "EV news, electric vehicles, charging"},
            {"domain": "jalopnik.com", "name": "Jalopnik", "what": "car culture, reviews, industry news"},
            {"domain": "insideevs.com", "name": "InsideEVs", "what": "electric vehicle sales, reviews, trends"},
        ],
        "closed": [
            {"name": "TikTok cars", "coverage_query": '"car tiktok" OR "cartok" OR "car review" tiktok trending'},
            {"name": "YouTube auto", "coverage_query": '"car youtube" OR "auto review youtube" trending viral'},
        ],
        "aggregators": [
            {"domain": "goodcarbadcar.net", "name": "GCBC", "what": "US auto sales data by model and brand"},
        ],
        "subreddits": ["r/cars", "r/electricvehicles", "r/Autos", "r/carporn"],
    },

    "Sports": {
        "crawlable": [
            {"domain": "espn.com", "name": "ESPN", "what": "scores, news, analysis across all sports"},
            {"domain": "theathletic.com", "name": "The Athletic", "what": "in-depth sports journalism"},
            {"domain": "bleacherreport.com", "name": "Bleacher Report", "what": "sports news, highlights, culture"},
            {"domain": "si.com", "name": "Sports Illustrated", "what": "features, rankings, athlete profiles"},
            {"domain": "deadspin.com", "name": "Deadspin", "what": "sports culture, media criticism"},
        ],
        "closed": [
            {"name": "TikTok sports", "coverage_query": '"sports tiktok" OR "sportstok" OR "nba tiktok" trending viral'},
            {"name": "Twitter/X sports", "coverage_query": '"sports twitter" OR "nba twitter" OR "nfl twitter" trending discussion'},
        ],
        "aggregators": [
            {"domain": "statmuse.com", "name": "StatMuse", "what": "sports stats and trending queries"},
        ],
        "subreddits": ["r/sports", "r/nba", "r/nfl", "r/soccer"],
    },

    "Entertainment and Pop Culture": {
        "crawlable": [
            {"domain": "variety.com", "name": "Variety", "what": "entertainment industry news, box office"},
            {"domain": "hollywoodreporter.com", "name": "Hollywood Reporter", "what": "film, TV, entertainment business"},
            {"domain": "ew.com", "name": "Entertainment Weekly", "what": "movies, TV, music, books reviews"},
            {"domain": "vulture.com", "name": "Vulture", "what": "pop culture criticism and features"},
            {"domain": "deadline.com", "name": "Deadline", "what": "entertainment industry breaking news"},
            {"domain": "rottentomatoes.com", "name": "Rotten Tomatoes", "what": "movie and TV ratings, trending titles"},
        ],
        "closed": [
            {"name": "TikTok pop culture", "coverage_query": '"trending on tiktok" celebrity OR movie OR show viral'},
            {"name": "Netflix", "coverage_query": '"netflix top 10" OR "netflix trending" OR "most watched netflix"'},
            {"name": "Letterboxd", "coverage_query": '"letterboxd" trending OR popular OR "most watched"'},
        ],
        "aggregators": [
            {"domain": "boxofficemojo.com", "name": "Box Office Mojo", "what": "box office revenue data and rankings"},
            {"domain": "justwatch.com", "name": "JustWatch", "what": "streaming availability and popularity"},
        ],
        "subreddits": ["r/movies", "r/television", "r/popculture", "r/entertainment"],
    },

    "Sustainability and Climate": {
        "crawlable": [
            {"domain": "treehugger.com", "name": "Treehugger", "what": "sustainability tips, green living"},
            {"domain": "grist.org", "name": "Grist", "what": "climate news, environmental justice"},
            {"domain": "theguardian.com/environment", "name": "Guardian Environment", "what": "climate journalism, policy"},
            {"domain": "ecowatch.com", "name": "EcoWatch", "what": "environmental news, renewable energy"},
            {"domain": "yaleclimateconnections.org", "name": "Yale Climate", "what": "climate science communication"},
        ],
        "closed": [
            {"name": "TikTok sustainability", "coverage_query": '"sustainability tiktok" OR "ecotok" OR "zero waste tiktok" trending'},
            {"name": "Instagram sustainability", "coverage_query": '"sustainability influencer" OR "eco influencer" instagram trending'},
        ],
        "aggregators": [
            {"domain": "ourworldindata.org", "name": "Our World in Data", "what": "climate and energy data visualizations"},
        ],
        "subreddits": ["r/sustainability", "r/ZeroWaste", "r/climate", "r/environment"],
    },

    "Home and Interior Design": {
        "crawlable": [
            {"domain": "architecturaldigest.com", "name": "Architectural Digest", "what": "home design, architecture, decor"},
            {"domain": "dwell.com", "name": "Dwell", "what": "modern architecture and interior design"},
            {"domain": "apartmenttherapy.com", "name": "Apartment Therapy", "what": "small space design, home tours, DIY"},
            {"domain": "housebeautiful.com", "name": "House Beautiful", "what": "decor trends, renovation, color trends"},
            {"domain": "dezeen.com", "name": "Dezeen", "what": "architecture, design, interiors news"},
        ],
        "closed": [
            {"name": "Pinterest home", "coverage_query": '"pinterest home decor" OR "pinterest interior" trending 2026'},
            {"name": "TikTok home", "coverage_query": '"hometok" OR "interior design tiktok" OR "home decor tiktok" trending'},
            {"name": "Instagram interiors", "coverage_query": '"interior design influencer" OR "home decor instagram" trending'},
        ],
        "aggregators": [],
        "subreddits": ["r/InteriorDesign", "r/HomeImprovement", "r/CozyPlaces", "r/malelivingspace"],
    },

    "Photography and Visual Arts": {
        "crawlable": [
            {"domain": "petapixel.com", "name": "PetaPixel", "what": "photography news, gear, techniques"},
            {"domain": "dpreview.com", "name": "DPReview", "what": "camera reviews, photography news"},
            {"domain": "fstoppers.com", "name": "Fstoppers", "what": "photography education, industry news"},
            {"domain": "thephoblographer.com", "name": "Phoblographer", "what": "camera reviews, photo culture"},
            {"domain": "colossal.art", "name": "Colossal", "what": "visual arts, installations, creativity"},
        ],
        "closed": [
            {"name": "Instagram photography", "coverage_query": '"photography instagram" OR "photographer instagram" trending viral'},
            {"name": "500px / Flickr", "coverage_query": '"500px trending" OR "flickr popular" photography trends'},
            {"name": "TikTok photography", "coverage_query": '"photography tiktok" OR "phototok" trending tips viral'},
        ],
        "aggregators": [],
        "subreddits": ["r/photography", "r/photocritique", "r/Art", "r/itookapicture"],
    },

    "Podcasting and Audio": {
        "crawlable": [
            {"domain": "podnews.net", "name": "Podnews", "what": "podcast industry news, charts, launches"},
            {"domain": "hotpodnews.com", "name": "Hot Pod", "what": "podcast business and culture"},
            {"domain": "podcast.apple.com", "name": "Apple Podcasts", "what": "podcast charts and categories"},
            {"domain": "theringer.com", "name": "The Ringer", "what": "pop culture podcasts, media criticism"},
            {"domain": "vulture.com/tag/podcasts", "name": "Vulture Podcasts", "what": "podcast reviews and features"},
        ],
        "closed": [
            {"name": "Spotify Podcasts", "coverage_query": '"spotify podcast" charts OR trending OR "top podcasts spotify"'},
            {"name": "YouTube podcasts", "coverage_query": '"youtube podcast" trending OR "video podcast" popular'},
            {"name": "TikTok audio", "coverage_query": '"podcast tiktok" OR "podcast clip" viral trending'},
        ],
        "aggregators": [
            {"domain": "chartable.com", "name": "Chartable", "what": "podcast rankings across platforms"},
            {"domain": "podtrac.com", "name": "Podtrac", "what": "podcast audience measurement and rankings"},
        ],
        "subreddits": ["r/podcasts", "r/podcasting", "r/audiodrama"],
    },

    "E-commerce and DTC": {
        "crawlable": [
            {"domain": "shopify.com/blog", "name": "Shopify Blog", "what": "e-commerce trends, merchant stories"},
            {"domain": "modernretail.co", "name": "Modern Retail", "what": "DTC brand news, e-commerce strategy"},
            {"domain": "retaildive.com", "name": "Retail Dive", "what": "retail industry news and trends"},
            {"domain": "2pml.com", "name": "2PM", "what": "DTC brand analysis, e-commerce strategy"},
            {"domain": "practicalecommerce.com", "name": "Practical Ecommerce", "what": "e-commerce tactics and tools"},
        ],
        "closed": [
            {"name": "TikTok Shop", "coverage_query": '"tiktok shop" trending OR "tiktok shop bestseller" OR "viral product tiktok"'},
            {"name": "Amazon trends", "coverage_query": '"amazon bestseller" OR "amazon trending" OR "amazon movers and shakers"'},
            {"name": "Instagram shopping", "coverage_query": '"instagram shop" OR "instagram shopping" trending products'},
        ],
        "aggregators": [
            {"domain": "jungle scout.com/blog", "name": "Jungle Scout", "what": "Amazon sales data and product trends"},
        ],
        "subreddits": ["r/ecommerce", "r/shopify", "r/FulfillmentByAmazon", "r/Entrepreneur"],
    },

    "Mental Health": {
        "crawlable": [
            {"domain": "psychologytoday.com", "name": "Psychology Today", "what": "mental health articles, therapy trends"},
            {"domain": "nami.org", "name": "NAMI", "what": "mental health advocacy, resources, news"},
            {"domain": "thecut.com", "name": "The Cut", "what": "psychology, relationships, culture"},
            {"domain": "greatergood.berkeley.edu", "name": "Greater Good", "what": "science of well-being, happiness research"},
            {"domain": "verywellmind.com", "name": "Verywell Mind", "what": "mental health conditions, coping, therapy"},
        ],
        "closed": [
            {"name": "TikTok mental health", "coverage_query": '"therapy tiktok" OR "mental health tiktok" OR "therapytok" trending'},
            {"name": "Instagram mental health", "coverage_query": '"mental health influencer" OR "therapy instagram" trending awareness'},
        ],
        "aggregators": [],
        "subreddits": ["r/mentalhealth", "r/anxiety", "r/depression", "r/therapy"],
    },

    "Crypto and Web3": {
        "crawlable": [
            {"domain": "coindesk.com", "name": "CoinDesk", "what": "crypto news, market analysis, regulation"},
            {"domain": "theblock.co", "name": "The Block", "what": "crypto and blockchain research, data"},
            {"domain": "decrypt.co", "name": "Decrypt", "what": "web3, NFTs, DeFi news and guides"},
            {"domain": "cointelegraph.com", "name": "CoinTelegraph", "what": "crypto market news, analysis"},
            {"domain": "defillama.com", "name": "DefiLlama", "what": "DeFi protocol TVL data and rankings"},
        ],
        "closed": [
            {"name": "Twitter/X crypto", "coverage_query": '"crypto twitter" OR "ct alpha" OR "web3 twitter" trending discussion'},
            {"name": "Discord crypto", "coverage_query": '"crypto discord" OR "nft discord" OR "web3 community" trending'},
        ],
        "aggregators": [
            {"domain": "coingecko.com", "name": "CoinGecko", "what": "crypto prices, trending coins, market data"},
            {"domain": "dune.com", "name": "Dune Analytics", "what": "on-chain data dashboards and trends"},
        ],
        "subreddits": ["r/CryptoCurrency", "r/ethereum", "r/defi", "r/NFT"],
    },
}

# Aliases so the lookup is forgiving with niche names
NICHE_ALIASES = {
    "tech": "AI and Tech",
    "technology": "AI and Tech",
    "ai": "AI and Tech",
    "ai and tech": "AI and Tech",
    "ai & tech": "AI and Tech",
    "music": "Music",
    "fitness": "Fitness",
    "food": "Food and Dining",
    "food and dining": "Food and Dining",
    "food & dining": "Food and Dining",
    "food and beverage": "Food and Dining",
    "gaming": "Gaming",
    "beauty": "Beauty and Skincare",
    "beauty and skincare": "Beauty and Skincare",
    "skincare": "Beauty and Skincare",
    "travel": "Travel and Outdoors",
    "travel and outdoors": "Travel and Outdoors",
    "outdoors": "Travel and Outdoors",
    "finance": "Finance and Investing",
    "finance and investing": "Finance and Investing",
    "investing": "Finance and Investing",
    "fintech": "Finance and Investing",
    "fashion": "Fashion",
    "education": "Education and Learning",
    "education and learning": "Education and Learning",
    "edtech": "Education and Learning",
    "learning": "Education and Learning",
    "health": "Health and Wellness",
    "health and wellness": "Health and Wellness",
    "wellness": "Health and Wellness",
    "parenting": "Parenting and Family",
    "parenting and family": "Parenting and Family",
    "family": "Parenting and Family",
    "pets": "Pets and Animals",
    "pets and animals": "Pets and Animals",
    "animals": "Pets and Animals",
    "real estate": "Real Estate",
    "property": "Real Estate",
    "housing": "Real Estate",
    "automotive": "Automotive",
    "cars": "Automotive",
    "auto": "Automotive",
    "ev": "Automotive",
    "electric vehicles": "Automotive",
    "sports": "Sports",
    "entertainment": "Entertainment and Pop Culture",
    "entertainment and pop culture": "Entertainment and Pop Culture",
    "pop culture": "Entertainment and Pop Culture",
    "movies": "Entertainment and Pop Culture",
    "tv": "Entertainment and Pop Culture",
    "sustainability": "Sustainability and Climate",
    "sustainability and climate": "Sustainability and Climate",
    "climate": "Sustainability and Climate",
    "environment": "Sustainability and Climate",
    "green": "Sustainability and Climate",
    "home": "Home and Interior Design",
    "home and interior design": "Home and Interior Design",
    "interior design": "Home and Interior Design",
    "home decor": "Home and Interior Design",
    "decor": "Home and Interior Design",
    "photography": "Photography and Visual Arts",
    "photography and visual arts": "Photography and Visual Arts",
    "visual arts": "Photography and Visual Arts",
    "podcasting": "Podcasting and Audio",
    "podcasting and audio": "Podcasting and Audio",
    "podcasts": "Podcasting and Audio",
    "audio": "Podcasting and Audio",
    "ecommerce": "E-commerce and DTC",
    "e-commerce": "E-commerce and DTC",
    "e-commerce and dtc": "E-commerce and DTC",
    "dtc": "E-commerce and DTC",
    "shopify": "E-commerce and DTC",
    "retail": "E-commerce and DTC",
    "mental health": "Mental Health",
    "therapy": "Mental Health",
    "psychology": "Mental Health",
    "crypto": "Crypto and Web3",
    "crypto and web3": "Crypto and Web3",
    "web3": "Crypto and Web3",
    "blockchain": "Crypto and Web3",
    "nft": "Crypto and Web3",
    "defi": "Crypto and Web3",
}


def get_sources_for_niche(niche: str):
    """
    Look up sources for a niche. Tries exact match first, then aliases.
    Returns None if the niche isn't in the registry (planner falls back
    to its own knowledge).
    """
    if niche in NICHE_SOURCES:
        return NICHE_SOURCES[niche]

    normalized = niche.lower().strip()
    alias_key = NICHE_ALIASES.get(normalized)
    if alias_key and alias_key in NICHE_SOURCES:
        return NICHE_SOURCES[alias_key]

    return None


def format_sources_for_prompt(niche: str) -> str:
    """
    Format the niche source registry into a text block the planner
    prompt can use directly.
    """
    sources = get_sources_for_niche(niche)
    if not sources:
        return ""

    lines = [f"=== NICHE SOURCE REGISTRY: {niche} ===\n"]

    lines.append("CRAWLABLE (use site: queries):")
    for s in sources.get("crawlable", []):
        lines.append(f"  - site:{s['domain']} — {s['name']}: {s['what']}")

    lines.append("\nCLOSED PLATFORMS (use coverage queries, NOT site:):")
    for s in sources.get("closed", []):
        lines.append(f"  - {s['name']}: search for → {s['coverage_query']}")

    lines.append("\nAGGREGATORS (crawlable proxies for closed platform data):")
    for s in sources.get("aggregators", []):
        lines.append(f"  - site:{s['domain']} — {s['name']}: {s['what']}")

    lines.append("\nREDDIT COMMUNITIES:")
    for sub in sources.get("subreddits", []):
        lines.append(f"  - site:reddit.com/{sub}")

    lines.append("\nUse at least 3 of these sources in your queries.")
    return "\n".join(lines)
