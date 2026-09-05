"""
LeakGrader.com - High-Scale 100,000 Daily Visitors Programmatic SEO Engine
Covers 315 Global Metros x 40 High-Ticket Commercial Verticals = 12,600+ Indexable Search Hubs.
Generates valid Google JSON-LD Schema (SoftwareApplication, LocalBusiness, FAQPage, BreadcrumbList).
"""

import json

CITIES_EXPANDED = [
    # --- USA (Top 100+ Metros) ---
    {"name": "New York", "slug": "new-york", "country": "United States", "region": "North America"},
    {"name": "Los Angeles", "slug": "los-angeles", "country": "United States", "region": "North America"},
    {"name": "Chicago", "slug": "chicago", "country": "United States", "region": "North America"},
    {"name": "Houston", "slug": "houston", "country": "United States", "region": "North America"},
    {"name": "Phoenix", "slug": "phoenix", "country": "United States", "region": "North America"},
    {"name": "Philadelphia", "slug": "philadelphia", "country": "United States", "region": "North America"},
    {"name": "San Antonio", "slug": "san-antonio", "country": "United States", "region": "North America"},
    {"name": "San Diego", "slug": "san-diego", "country": "United States", "region": "North America"},
    {"name": "Dallas", "slug": "dallas", "country": "United States", "region": "North America"},
    {"name": "Austin", "slug": "austin", "country": "United States", "region": "North America"},
    {"name": "San Jose", "slug": "san-jose", "country": "United States", "region": "North America"},
    {"name": "Fort Worth", "slug": "fort-worth", "country": "United States", "region": "North America"},
    {"name": "Columbus", "slug": "columbus", "country": "United States", "region": "North America"},
    {"name": "Charlotte", "slug": "charlotte", "country": "United States", "region": "North America"},
    {"name": "Indianapolis", "slug": "indianapolis", "country": "United States", "region": "North America"},
    {"name": "San Francisco", "slug": "san-francisco", "country": "United States", "region": "North America"},
    {"name": "Seattle", "slug": "seattle", "country": "United States", "region": "North America"},
    {"name": "Denver", "slug": "denver", "country": "United States", "region": "North America"},
    {"name": "Oklahoma City", "slug": "oklahoma-city", "country": "United States", "region": "North America"},
    {"name": "Nashville", "slug": "nashville", "country": "United States", "region": "North America"},
    {"name": "El Paso", "slug": "el-paso", "country": "United States", "region": "North America"},
    {"name": "Washington", "slug": "washington-dc", "country": "United States", "region": "North America"},
    {"name": "Boston", "slug": "boston", "country": "United States", "region": "North America"},
    {"name": "Las Vegas", "slug": "las-vegas", "country": "United States", "region": "North America"},
    {"name": "Portland", "slug": "portland", "country": "United States", "region": "North America"},
    {"name": "Detroit", "slug": "detroit", "country": "United States", "region": "North America"},
    {"name": "Louisville", "slug": "louisville", "country": "United States", "region": "North America"},
    {"name": "Memphis", "slug": "memphis", "country": "United States", "region": "North America"},
    {"name": "Baltimore", "slug": "baltimore", "country": "United States", "region": "North America"},
    {"name": "Milwaukee", "slug": "milwaukee", "country": "United States", "region": "North America"},
    {"name": "Albuquerque", "slug": "albuquerque", "country": "United States", "region": "North America"},
    {"name": "Tucson", "slug": "tucson", "country": "United States", "region": "North America"},
    {"name": "Fresno", "slug": "fresno", "country": "United States", "region": "North America"},
    {"name": "Sacramento", "slug": "sacramento", "country": "United States", "region": "North America"},
    {"name": "Mesa", "slug": "mesa", "country": "United States", "region": "North America"},
    {"name": "Kansas City", "slug": "kansas-city", "country": "United States", "region": "North America"},
    {"name": "Atlanta", "slug": "atlanta", "country": "United States", "region": "North America"},
    {"name": "Omaha", "slug": "omaha", "country": "United States", "region": "North America"},
    {"name": "Colorado Springs", "slug": "colorado-springs", "country": "United States", "region": "North America"},
    {"name": "Raleigh", "slug": "raleigh", "country": "United States", "region": "North America"},
    {"name": "Long Beach", "slug": "long-beach", "country": "United States", "region": "North America"},
    {"name": "Virginia Beach", "slug": "virginia-beach", "country": "United States", "region": "North America"},
    {"name": "Miami", "slug": "miami", "country": "United States", "region": "North America"},
    {"name": "Oakland", "slug": "oakland", "country": "United States", "region": "North America"},
    {"name": "Minneapolis", "slug": "minneapolis", "country": "United States", "region": "North America"},
    {"name": "Tulsa", "slug": "tulsa", "country": "United States", "region": "North America"},
    {"name": "Tampa", "slug": "tampa", "country": "United States", "region": "North America"},
    {"name": "Arlington", "slug": "arlington", "country": "United States", "region": "North America"},
    {"name": "New Orleans", "slug": "new-orleans", "country": "United States", "region": "North America"},
    {"name": "Wichita", "slug": "wichita", "country": "United States", "region": "North America"},
    {"name": "Cleveland", "slug": "cleveland", "country": "United States", "region": "North America"},
    {"name": "Bakersfield", "slug": "bakersfield", "country": "United States", "region": "North America"},
    {"name": "Aurora", "slug": "aurora", "country": "United States", "region": "North America"},
    {"name": "Anaheim", "slug": "anaheim", "country": "United States", "region": "North America"},
    {"name": "Honolulu", "slug": "honolulu", "country": "United States", "region": "North America"},
    {"name": "Santa Ana", "slug": "santa-ana", "country": "United States", "region": "North America"},
    {"name": "Riverside", "slug": "riverside", "country": "United States", "region": "North America"},
    {"name": "Corpus Christi", "slug": "corpus-christi", "country": "United States", "region": "North America"},
    {"name": "Lexington", "slug": "lexington", "country": "United States", "region": "North America"},
    {"name": "Stockton", "slug": "stockton", "country": "United States", "region": "North America"},
    {"name": "Henderson", "slug": "henderson", "country": "United States", "region": "North America"},
    {"name": "Saint Paul", "slug": "saint-paul", "country": "United States", "region": "North America"},
    {"name": "St. Louis", "slug": "st-louis", "country": "United States", "region": "North America"},
    {"name": "Cincinnati", "slug": "cincinnati", "country": "United States", "region": "North America"},
    {"name": "Pittsburgh", "slug": "pittsburgh", "country": "United States", "region": "North America"},
    {"name": "Greensboro", "slug": "greensboro", "country": "United States", "region": "North America"},
    {"name": "Anchorage", "slug": "anchorage", "country": "United States", "region": "North America"},
    {"name": "Plano", "slug": "plano", "country": "United States", "region": "North America"},
    {"name": "Lincoln", "slug": "lincoln", "country": "United States", "region": "North America"},
    {"name": "Orlando", "slug": "orlando", "country": "United States", "region": "North America"},
    {"name": "Irvine", "slug": "irvine", "country": "United States", "region": "North America"},
    {"name": "Newark", "slug": "newark", "country": "United States", "region": "North America"},
    {"name": "Toledo", "slug": "toledo", "country": "United States", "region": "North America"},
    {"name": "Durham", "slug": "durham", "country": "United States", "region": "North America"},
    {"name": "Chula Vista", "slug": "chula-vista", "country": "United States", "region": "North America"},
    {"name": "Fort Wayne", "slug": "fort-wayne", "country": "United States", "region": "North America"},
    {"name": "Jersey City", "slug": "jersey-city", "country": "United States", "region": "North America"},
    {"name": "St. Petersburg", "slug": "st-petersburg", "country": "United States", "region": "North America"},
    {"name": "Laredo", "slug": "laredo", "country": "United States", "region": "North America"},
    {"name": "Madison", "slug": "madison", "country": "United States", "region": "North America"},
    {"name": "Chandler", "slug": "chandler", "country": "United States", "region": "North America"},
    {"name": "Buffalo", "slug": "buffalo", "country": "United States", "region": "North America"},
    {"name": "Lubbock", "slug": "lubbock", "country": "United States", "region": "North America"},
    {"name": "Scottsdale", "slug": "scottsdale", "country": "United States", "region": "North America"},
    {"name": "Reno", "slug": "reno", "country": "United States", "region": "North America"},
    {"name": "Glendale", "slug": "glendale", "country": "United States", "region": "North America"},
    {"name": "Gilbert", "slug": "gilbert", "country": "United States", "region": "North America"},
    {"name": "Winston-Salem", "slug": "winston-salem", "country": "United States", "region": "North America"},
    {"name": "North Las Vegas", "slug": "north-las-vegas", "country": "United States", "region": "North America"},
    {"name": "Norfolk", "slug": "norfolk", "country": "United States", "region": "North America"},
    {"name": "Chesapeake", "slug": "chesapeake", "country": "United States", "region": "North America"},
    {"name": "Garland", "slug": "garland", "country": "United States", "region": "North America"},
    {"name": "Irving", "slug": "irving", "country": "United States", "region": "North America"},
    {"name": "Hialeah", "slug": "hialeah", "country": "United States", "region": "North America"},
    {"name": "Fremont", "slug": "fremont", "country": "United States", "region": "North America"},
    {"name": "Boise", "slug": "boise", "country": "United States", "region": "North America"},
    {"name": "Richmond", "slug": "richmond", "country": "United States", "region": "North America"},
    {"name": "Baton Rouge", "slug": "baton-rouge", "country": "United States", "region": "North America"},
    {"name": "Spokane", "slug": "spokane", "country": "United States", "region": "North America"},
    {"name": "Des Moines", "slug": "des-moines", "country": "United States", "region": "North America"},

    # --- Canada (25 Cities) ---
    {"name": "Toronto", "slug": "toronto", "country": "Canada", "region": "North America"},
    {"name": "Montreal", "slug": "montreal", "country": "Canada", "region": "North America"},
    {"name": "Vancouver", "slug": "vancouver", "country": "Canada", "region": "North America"},
    {"name": "Calgary", "slug": "calgary", "country": "Canada", "region": "North America"},
    {"name": "Edmonton", "slug": "edmonton", "country": "Canada", "region": "North America"},
    {"name": "Ottawa", "slug": "ottawa", "country": "Canada", "region": "North America"},
    {"name": "Winnipeg", "slug": "winnipeg", "country": "Canada", "region": "North America"},
    {"name": "Quebec City", "slug": "quebec-city", "country": "Canada", "region": "North America"},
    {"name": "Hamilton", "slug": "hamilton", "country": "Canada", "region": "North America"},
    {"name": "Kitchener", "slug": "kitchener", "country": "Canada", "region": "North America"},
    {"name": "London", "slug": "london-ca", "country": "Canada", "region": "North America"},
    {"name": "Victoria", "slug": "victoria", "country": "Canada", "region": "North America"},
    {"name": "Halifax", "slug": "halifax", "country": "Canada", "region": "North America"},
    {"name": "Oshawa", "slug": "oshawa", "country": "Canada", "region": "North America"},
    {"name": "Windsor", "slug": "windsor", "country": "Canada", "region": "North America"},
    {"name": "Saskatoon", "slug": "saskatoon", "country": "Canada", "region": "North America"},
    {"name": "Regina", "slug": "regina", "country": "Canada", "region": "North America"},
    {"name": "St. John's", "slug": "st-johns", "country": "Canada", "region": "North America"},
    {"name": "Kelowna", "slug": "kelowna", "country": "Canada", "region": "North America"},
    {"name": "Barrie", "slug": "barrie", "country": "Canada", "region": "North America"},
    {"name": "Sherbrooke", "slug": "sherbrooke", "country": "Canada", "region": "North America"},
    {"name": "Guelph", "slug": "guelph", "country": "Canada", "region": "North America"},
    {"name": "Kanata", "slug": "kanata", "country": "Canada", "region": "North America"},
    {"name": "Abbotsford", "slug": "abbotsford", "country": "Canada", "region": "North America"},
    {"name": "Kingston", "slug": "kingston", "country": "Canada", "region": "North America"},

    # --- Australia (20 Cities) ---
    {"name": "Sydney", "slug": "sydney", "country": "Australia", "region": "Asia Pacific"},
    {"name": "Melbourne", "slug": "melbourne", "country": "Australia", "region": "Asia Pacific"},
    {"name": "Brisbane", "slug": "brisbane", "country": "Australia", "region": "Asia Pacific"},
    {"name": "Perth", "slug": "perth", "country": "Australia", "region": "Asia Pacific"},
    {"name": "Adelaide", "slug": "adelaide", "country": "Australia", "region": "Asia Pacific"},
    {"name": "Gold Coast", "slug": "gold-coast", "country": "Australia", "region": "Asia Pacific"},
    {"name": "Newcastle", "slug": "newcastle-au", "country": "Australia", "region": "Asia Pacific"},
    {"name": "Canberra", "slug": "canberra", "country": "Australia", "region": "Asia Pacific"},
    {"name": "Sunshine Coast", "slug": "sunshine-coast", "country": "Australia", "region": "Asia Pacific"},
    {"name": "Wollongong", "slug": "wollongong", "country": "Australia", "region": "Asia Pacific"},
    {"name": "Geelong", "slug": "geelong", "country": "Australia", "region": "Asia Pacific"},
    {"name": "Hobart", "slug": "hobart", "country": "Australia", "region": "Asia Pacific"},
    {"name": "Townsville", "slug": "townsville", "country": "Australia", "region": "Asia Pacific"},
    {"name": "Cairns", "slug": "cairns", "country": "Australia", "region": "Asia Pacific"},
    {"name": "Toowoomba", "slug": "toowoomba", "country": "Australia", "region": "Asia Pacific"},
    {"name": "Darwin", "slug": "darwin", "country": "Australia", "region": "Asia Pacific"},
    {"name": "Ballarat", "slug": "ballarat", "country": "Australia", "region": "Asia Pacific"},
    {"name": "Bendigo", "slug": "bendigo", "country": "Australia", "region": "Asia Pacific"},
    {"name": "Albury", "slug": "albury", "country": "Australia", "region": "Asia Pacific"},
    {"name": "Launceston", "slug": "launceston", "country": "Australia", "region": "Asia Pacific"},

    # --- United Kingdom (25 Cities) ---
    {"name": "London", "slug": "london", "country": "United Kingdom", "region": "Europe"},
    {"name": "Birmingham", "slug": "birmingham", "country": "United Kingdom", "region": "Europe"},
    {"name": "Manchester", "slug": "manchester", "country": "United Kingdom", "region": "Europe"},
    {"name": "Glasgow", "slug": "glasgow", "country": "United Kingdom", "region": "Europe"},
    {"name": "Leeds", "slug": "leeds", "country": "United Kingdom", "region": "Europe"},
    {"name": "Liverpool", "slug": "liverpool", "country": "United Kingdom", "region": "Europe"},
    {"name": "Newcastle", "slug": "newcastle", "country": "United Kingdom", "region": "Europe"},
    {"name": "Sheffield", "slug": "sheffield", "country": "United Kingdom", "region": "Europe"},
    {"name": "Bristol", "slug": "bristol", "country": "United Kingdom", "region": "Europe"},
    {"name": "Belfast", "slug": "belfast", "country": "United Kingdom", "region": "Europe"},
    {"name": "Edinburgh", "slug": "edinburgh", "country": "United Kingdom", "region": "Europe"},
    {"name": "Leicester", "slug": "leicester", "country": "United Kingdom", "region": "Europe"},
    {"name": "Nottingham", "slug": "nottingham", "country": "United Kingdom", "region": "Europe"},
    {"name": "Southampton", "slug": "southampton", "country": "United Kingdom", "region": "Europe"},
    {"name": "Coventry", "slug": "coventry", "country": "United Kingdom", "region": "Europe"},
    {"name": "Hull", "slug": "hull", "country": "United Kingdom", "region": "Europe"},
    {"name": "Bradford", "slug": "bradford", "country": "United Kingdom", "region": "Europe"},
    {"name": "Cardiff", "slug": "cardiff", "country": "United Kingdom", "region": "Europe"},
    {"name": "Stoke-on-Trent", "slug": "stoke-on-trent", "country": "United Kingdom", "region": "Europe"},
    {"name": "Wolverhampton", "slug": "wolverhampton", "country": "United Kingdom", "region": "Europe"},
    {"name": "Plymouth", "slug": "plymouth", "country": "United Kingdom", "region": "Europe"},
    {"name": "Derby", "slug": "derby", "country": "United Kingdom", "region": "Europe"},
    {"name": "Reading", "slug": "reading", "country": "United Kingdom", "region": "Europe"},
    {"name": "Cambridge", "slug": "cambridge", "country": "United Kingdom", "region": "Europe"},
    {"name": "Oxford", "slug": "oxford", "country": "United Kingdom", "region": "Europe"},

    # --- France (20 Cities) ---
    {"name": "Paris", "slug": "paris", "country": "France", "region": "Europe"},
    {"name": "Marseille", "slug": "marseille", "country": "France", "region": "Europe"},
    {"name": "Lyon", "slug": "lyon", "country": "France", "region": "Europe"},
    {"name": "Toulouse", "slug": "toulouse", "country": "France", "region": "Europe"},
    {"name": "Nice", "slug": "nice", "country": "France", "region": "Europe"},
    {"name": "Nantes", "slug": "nantes", "country": "France", "region": "Europe"},
    {"name": "Montpellier", "slug": "montpellier", "country": "France", "region": "Europe"},
    {"name": "Strasbourg", "slug": "strasbourg", "country": "France", "region": "Europe"},
    {"name": "Bordeaux", "slug": "bordeaux", "country": "France", "region": "Europe"},
    {"name": "Lille", "slug": "lille", "country": "France", "region": "Europe"},
    {"name": "Rennes", "slug": "rennes", "country": "France", "region": "Europe"},
    {"name": "Reims", "slug": "reims", "country": "France", "region": "Europe"},
    {"name": "Saint-Etienne", "slug": "saint-etienne", "country": "France", "region": "Europe"},
    {"name": "Le Havre", "slug": "le-havre", "country": "France", "region": "Europe"},
    {"name": "Toulon", "slug": "toulon", "country": "France", "region": "Europe"},
    {"name": "Grenoble", "slug": "grenoble", "country": "France", "region": "Europe"},
    {"name": "Dijon", "slug": "dijon", "country": "France", "region": "Europe"},
    {"name": "Angers", "slug": "angers", "country": "France", "region": "Europe"},
    {"name": "Nimes", "slug": "nimes", "country": "France", "region": "Europe"},
    {"name": "Villeurbanne", "slug": "villeurbanne", "country": "France", "region": "Europe"},

    # --- Germany (20 Cities) ---
    {"name": "Berlin", "slug": "berlin", "country": "Germany", "region": "Europe"},
    {"name": "Hamburg", "slug": "hamburg", "country": "Germany", "region": "Europe"},
    {"name": "Munich", "slug": "munich", "country": "Germany", "region": "Europe"},
    {"name": "Cologne", "slug": "cologne", "country": "Germany", "region": "Europe"},
    {"name": "Frankfurt", "slug": "frankfurt", "country": "Germany", "region": "Europe"},
    {"name": "Stuttgart", "slug": "stuttgart", "country": "Germany", "region": "Europe"},
    {"name": "Dusseldorf", "slug": "dusseldorf", "country": "Germany", "region": "Europe"},
    {"name": "Leipzig", "slug": "leipzig", "country": "Germany", "region": "Europe"},
    {"name": "Dortmund", "slug": "dortmund", "country": "Germany", "region": "Europe"},
    {"name": "Essen", "slug": "essen", "country": "Germany", "region": "Europe"},
    {"name": "Bremen", "slug": "bremen", "country": "Germany", "region": "Europe"},
    {"name": "Dresden", "slug": "dresden", "country": "Germany", "region": "Europe"},
    {"name": "Hanover", "slug": "hanover", "country": "Germany", "region": "Europe"},
    {"name": "Nuremberg", "slug": "nuremberg", "country": "Germany", "region": "Europe"},
    {"name": "Duisburg", "slug": "duisburg", "country": "Germany", "region": "Europe"},
    {"name": "Bochum", "slug": "bochum", "country": "Germany", "region": "Europe"},
    {"name": "Wuppertal", "slug": "wuppertal", "country": "Germany", "region": "Europe"},
    {"name": "Bielefeld", "slug": "bielefeld", "country": "Germany", "region": "Europe"},
    {"name": "Bonn", "slug": "bonn", "country": "Germany", "region": "Europe"},
    {"name": "Munster", "slug": "munster", "country": "Germany", "region": "Europe"},

    # --- Japan (15 Cities) ---
    {"name": "Tokyo", "slug": "tokyo", "country": "Japan", "region": "Asia Pacific"},
    {"name": "Yokohama", "slug": "yokohama", "country": "Japan", "region": "Asia Pacific"},
    {"name": "Osaka", "slug": "osaka", "country": "Japan", "region": "Asia Pacific"},
    {"name": "Nagoya", "slug": "nagoya", "country": "Japan", "region": "Asia Pacific"},
    {"name": "Sapporo", "slug": "sapporo", "country": "Japan", "region": "Asia Pacific"},
    {"name": "Fukuoka", "slug": "fukuoka", "country": "Japan", "region": "Asia Pacific"},
    {"name": "Kobe", "slug": "kobe", "country": "Japan", "region": "Asia Pacific"},
    {"name": "Kyoto", "slug": "kyoto", "country": "Japan", "region": "Asia Pacific"},
    {"name": "Kawasaki", "slug": "kawasaki", "country": "Japan", "region": "Asia Pacific"},
    {"name": "Saitama", "slug": "saitama", "country": "Japan", "region": "Asia Pacific"},
    {"name": "Hiroshima", "slug": "hiroshima", "country": "Japan", "region": "Asia Pacific"},
    {"name": "Sendai", "slug": "sendai", "country": "Japan", "region": "Asia Pacific"},
    {"name": "Chiba", "slug": "chiba", "country": "Japan", "region": "Asia Pacific"},
    {"name": "Kitakyushu", "slug": "kitakyushu", "country": "Japan", "region": "Asia Pacific"},
    {"name": "Shizuoka", "slug": "shizuoka", "country": "Japan", "region": "Asia Pacific"},

    # --- South Korea (10 Cities) ---
    {"name": "Seoul", "slug": "seoul", "country": "South Korea", "region": "Asia Pacific"},
    {"name": "Busan", "slug": "busan", "country": "South Korea", "region": "Asia Pacific"},
    {"name": "Incheon", "slug": "incheon", "country": "South Korea", "region": "Asia Pacific"},
    {"name": "Daegu", "slug": "daegu", "country": "South Korea", "region": "Asia Pacific"},
    {"name": "Daejeon", "slug": "daejeon", "country": "South Korea", "region": "Asia Pacific"},
    {"name": "Gwangju", "slug": "gwangju", "country": "South Korea", "region": "Asia Pacific"},
    {"name": "Suwon", "slug": "suwon", "country": "South Korea", "region": "Asia Pacific"},
    {"name": "Ulsan", "slug": "ulsan", "country": "South Korea", "region": "Asia Pacific"},
    {"name": "Changwon", "slug": "changwon", "country": "South Korea", "region": "Asia Pacific"},
    {"name": "Seongnam", "slug": "seongnam", "country": "South Korea", "region": "Asia Pacific"},

    # --- India (25 Cities) ---
    {"name": "Mumbai", "slug": "mumbai", "country": "India", "region": "Asia Pacific"},
    {"name": "Delhi", "slug": "delhi", "country": "India", "region": "Asia Pacific"},
    {"name": "Bangalore", "slug": "bangalore", "country": "India", "region": "Asia Pacific"},
    {"name": "Hyderabad", "slug": "hyderabad", "country": "India", "region": "Asia Pacific"},
    {"name": "Ahmedabad", "slug": "ahmedabad", "country": "India", "region": "Asia Pacific"},
    {"name": "Chennai", "slug": "chennai", "country": "India", "region": "Asia Pacific"},
    {"name": "Kolkata", "slug": "kolkata", "country": "India", "region": "Asia Pacific"},
    {"name": "Surat", "slug": "surat", "country": "India", "region": "Asia Pacific"},
    {"name": "Pune", "slug": "pune", "country": "India", "region": "Asia Pacific"},
    {"name": "Jaipur", "slug": "jaipur", "country": "India", "region": "Asia Pacific"},
    {"name": "Lucknow", "slug": "lucknow", "country": "India", "region": "Asia Pacific"},
    {"name": "Kanpur", "slug": "kanpur", "country": "India", "region": "Asia Pacific"},
    {"name": "Nagpur", "slug": "nagpur", "country": "India", "region": "Asia Pacific"},
    {"name": "Indore", "slug": "indore", "country": "India", "region": "Asia Pacific"},
    {"name": "Thane", "slug": "thane", "country": "India", "region": "Asia Pacific"},
    {"name": "Bhopal", "slug": "bhopal", "country": "India", "region": "Asia Pacific"},
    {"name": "Visakhapatnam", "slug": "visakhapatnam", "country": "India", "region": "Asia Pacific"},
    {"name": "Patna", "slug": "patna", "country": "India", "region": "Asia Pacific"},
    {"name": "Vadodara", "slug": "vadodara", "country": "India", "region": "Asia Pacific"},
    {"name": "Ghaziabad", "slug": "ghaziabad", "country": "India", "region": "Asia Pacific"},
    {"name": "Ludhiana", "slug": "ludhiana", "country": "India", "region": "Asia Pacific"},
    {"name": "Agra", "slug": "agra", "country": "India", "region": "Asia Pacific"},
    {"name": "Nashik", "slug": "nashik", "country": "India", "region": "Asia Pacific"},
    {"name": "Faridabad", "slug": "faridabad", "country": "India", "region": "Asia Pacific"},
    {"name": "Coimbatore", "slug": "coimbatore", "country": "India", "region": "Asia Pacific"},

    # --- Philippines (15 Cities) ---
    {"name": "Manila", "slug": "manila", "country": "Philippines", "region": "Asia Pacific"},
    {"name": "Quezon City", "slug": "quezon-city", "country": "Philippines", "region": "Asia Pacific"},
    {"name": "Davao City", "slug": "davao-city", "country": "Philippines", "region": "Asia Pacific"},
    {"name": "Cebu City", "slug": "cebu", "country": "Philippines", "region": "Asia Pacific"},
    {"name": "Caloocan", "slug": "caloocan", "country": "Philippines", "region": "Asia Pacific"},
    {"name": "Zamboanga City", "slug": "zamboanga", "country": "Philippines", "region": "Asia Pacific"},
    {"name": "Taguig", "slug": "taguig", "country": "Philippines", "region": "Asia Pacific"},
    {"name": "Pasig", "slug": "pasig", "country": "Philippines", "region": "Asia Pacific"},
    {"name": "Cagayan de Oro", "slug": "cagayan-de-oro", "country": "Philippines", "region": "Asia Pacific"},
    {"name": "Paranaque", "slug": "paranaque", "country": "Philippines", "region": "Asia Pacific"},
    {"name": "Makati", "slug": "makati", "country": "Philippines", "region": "Asia Pacific"},
    {"name": "Bacolod", "slug": "bacolod", "country": "Philippines", "region": "Asia Pacific"},
    {"name": "Pasay", "slug": "pasay", "country": "Philippines", "region": "Asia Pacific"},
    {"name": "Angeles City", "slug": "angeles-city", "country": "Philippines", "region": "Asia Pacific"},
    {"name": "Iloilo City", "slug": "iloilo-city", "country": "Philippines", "region": "Asia Pacific"},

    # --- Middle East & Gulf (15 Cities) ---
    {"name": "Dubai", "slug": "dubai", "country": "United Arab Emirates", "region": "Middle East"},
    {"name": "Abu Dhabi", "slug": "abu-dhabi", "country": "United Arab Emirates", "region": "Middle East"},
    {"name": "Riyadh", "slug": "riyadh", "country": "Saudi Arabia", "region": "Middle East"},
    {"name": "Jeddah", "slug": "jeddah", "country": "Saudi Arabia", "region": "Middle East"},
    {"name": "Doha", "slug": "doha", "country": "Qatar", "region": "Middle East"},
    {"name": "Kuwait City", "slug": "kuwait-city", "country": "Kuwait", "region": "Middle East"},
    {"name": "Manama", "slug": "manama", "country": "Bahrain", "region": "Middle East"},
    {"name": "Muscat", "slug": "muscat", "country": "Oman", "region": "Middle East"},
    {"name": "Sharjah", "slug": "sharjah", "country": "United Arab Emirates", "region": "Middle East"},
    {"name": "Dammam", "slug": "dammam", "country": "Saudi Arabia", "region": "Middle East"},
    {"name": "Mecca", "slug": "mecca", "country": "Saudi Arabia", "region": "Middle East"},
    {"name": "Medina", "slug": "medina", "country": "Saudi Arabia", "region": "Middle East"},
    {"name": "Khobar", "slug": "khobar", "country": "Saudi Arabia", "region": "Middle East"},
    {"name": "Ajman", "slug": "ajman", "country": "United Arab Emirates", "region": "Middle East"},
    {"name": "Ras Al Khaimah", "slug": "ras-al-khaimah", "country": "United Arab Emirates", "region": "Middle East"},

    # --- Other Tier-1 Global Hubs (25 Cities) ---
    {"name": "Zurich", "slug": "zurich", "country": "Switzerland", "region": "Europe"},
    {"name": "Geneva", "slug": "geneva", "country": "Switzerland", "region": "Europe"},
    {"name": "Amsterdam", "slug": "amsterdam", "country": "Netherlands", "region": "Europe"},
    {"name": "Rotterdam", "slug": "rotterdam", "country": "Netherlands", "region": "Europe"},
    {"name": "Dublin", "slug": "dublin", "country": "Ireland", "region": "Europe"},
    {"name": "Stockholm", "slug": "stockholm", "country": "Sweden", "region": "Europe"},
    {"name": "Madrid", "slug": "madrid", "country": "Spain", "region": "Europe"},
    {"name": "Barcelona", "slug": "barcelona", "country": "Spain", "region": "Europe"},
    {"name": "Milan", "slug": "milan", "country": "Italy", "region": "Europe"},
    {"name": "Rome", "slug": "rome", "country": "Italy", "region": "Europe"},
    {"name": "Vienna", "slug": "vienna", "country": "Austria", "region": "Europe"},
    {"name": "Brussels", "slug": "brussels", "country": "Belgium", "region": "Europe"},
    {"name": "Copenhagen", "slug": "copenhagen", "country": "Denmark", "region": "Europe"},
    {"name": "Oslo", "slug": "oslo", "country": "Norway", "region": "Europe"},
    {"name": "Helsinki", "slug": "helsinki", "country": "Finland", "region": "Europe"},
    {"name": "Singapore", "slug": "singapore", "country": "Singapore", "region": "Asia Pacific"},
    {"name": "Hong Kong", "slug": "hong-kong", "country": "Hong Kong", "region": "Asia Pacific"},
    {"name": "Auckland", "slug": "auckland", "country": "New Zealand", "region": "Asia Pacific"},
    {"name": "Wellington", "slug": "wellington", "country": "New Zealand", "region": "Asia Pacific"},
    {"name": "Lisbon", "slug": "lisbon", "country": "Portugal", "region": "Europe"},
    {"name": "Prague", "slug": "prague", "country": "Czech Republic", "region": "Europe"},
    {"name": "Warsaw", "slug": "warsaw", "country": "Poland", "region": "Europe"},
    {"name": "Athens", "slug": "athens", "country": "Greece", "region": "Europe"},
    {"name": "Budapest", "slug": "budapest", "country": "Hungary", "region": "Europe"},
    {"name": "Tel Aviv", "slug": "tel-aviv", "country": "Israel", "region": "Middle East"}
]

NICHES_EXPANDED = [
    {"name": "Luxury Real Estate & Brokerages", "slug": "real-estate", "avg_deal": "$75,000", "avg_leak": "$52,000/mo"},
    {"name": "Private Dental Clinics & Implants", "slug": "dental-clinics", "avg_deal": "$8,500", "avg_leak": "$28,000/mo"},
    {"name": "Cosmetic & Plastic Surgery Centers", "slug": "plastic-surgery", "avg_deal": "$18,000", "avg_leak": "$45,000/mo"},
    {"name": "Corporate Law & Litigation Firms", "slug": "law-firms", "avg_deal": "$35,000", "avg_leak": "$65,000/mo"},
    {"name": "Wealth Management & Family Offices", "slug": "wealth-management", "avg_deal": "$120,000", "avg_leak": "$95,000/mo"},
    {"name": "B2B SaaS & AI Software Platforms", "slug": "b2b-saas", "avg_deal": "$25,000", "avg_leak": "$48,000/mo"},
    {"name": "Private Equity & Venture Capital", "slug": "private-equity", "avg_deal": "$250,000", "avg_leak": "$150,000/mo"},
    {"name": "Commercial HVAC & Mechanical", "slug": "commercial-hvac", "avg_deal": "$45,000", "avg_leak": "$38,000/mo"},
    {"name": "Yacht Charter & Luxury Marine", "slug": "yacht-charters", "avg_deal": "$60,000", "avg_leak": "$55,000/mo"},
    {"name": "Luxury Car Dealerships & Exotics", "slug": "exotic-cars", "avg_deal": "$85,000", "avg_leak": "$62,000/mo"},
    {"name": "Commercial Roofing & Solar EPC", "slug": "commercial-roofing", "avg_deal": "$55,000", "avg_leak": "$42,000/mo"},
    {"name": "Executive Recruitment & Headhunting", "slug": "executive-search", "avg_deal": "$30,000", "avg_leak": "$36,000/mo"},
    {"name": "MedSpa & Anti-Aging Clinics", "slug": "medspa", "avg_deal": "$6,500", "avg_leak": "$24,000/mo"},
    {"name": "Architecture & High-End Interior Design", "slug": "architecture-design", "avg_deal": "$40,000", "avg_leak": "$39,000/mo"},
    {"name": "IT Managed Services (MSPs)", "slug": "it-msp", "avg_deal": "$18,000", "avg_leak": "$32,000/mo"},
    {"name": "Logistics & Freight Forwarding", "slug": "logistics-freight", "avg_deal": "$50,000", "avg_leak": "$44,000/mo"},
    {"name": "Cybersecurity & Compliance Advisory", "slug": "cybersecurity", "avg_deal": "$65,000", "avg_leak": "$58,000/mo"},
    {"name": "Investment Migration & Citizenship", "slug": "citizenship-by-investment", "avg_deal": "$100,000", "avg_leak": "$88,000/mo"},
    {"name": "High-Ticket E-Commerce Brands", "slug": "high-ticket-ecommerce", "avg_deal": "$4,500", "avg_leak": "$35,000/mo"},
    {"name": "Specialty Medical & Fertility Centers", "slug": "fertility-clinics", "avg_deal": "$22,000", "avg_leak": "$40,000/mo"},
    {"name": "Private Jet Charter & Aviation", "slug": "private-jets", "avg_deal": "$95,000", "avg_leak": "$80,000/mo"},
    {"name": "Commercial Real Estate Brokerage", "slug": "commercial-real-estate", "avg_deal": "$110,000", "avg_leak": "$75,000/mo"},
    {"name": "Boutique Accounting & Tax Advisory", "slug": "accounting-tax", "avg_deal": "$20,000", "avg_leak": "$30,000/mo"},
    {"name": "Orthopedic & Spine Surgery Clinics", "slug": "orthopedic-surgery", "avg_deal": "$30,000", "avg_leak": "$50,000/mo"},
    {"name": "M&A Advisory & Business Brokers", "slug": "ma-advisory", "avg_deal": "$180,000", "avg_leak": "$120,000/mo"},
    {"name": "Custom Home Builders & General Contractors", "slug": "custom-home-builders", "avg_deal": "$85,000", "avg_leak": "$60,000/mo"},
    {"name": "High-End Event & Wedding Planning", "slug": "luxury-events", "avg_deal": "$25,000", "avg_leak": "$22,000/mo"},
    {"name": "Biohacking & Longevity Medicine", "slug": "longevity-clinics", "avg_deal": "$15,000", "avg_leak": "$35,000/mo"},
    {"name": "Industrial Equipment & Machinery Suppliers", "slug": "industrial-equipment", "avg_deal": "$70,000", "avg_leak": "$55,000/mo"},
    {"name": "High-Net-Worth Insurance Brokers", "slug": "hnw-insurance", "avg_deal": "$40,000", "avg_leak": "$45,000/mo"},
    {"name": "Intellectual Property & Patent Attorneys", "slug": "patent-law", "avg_deal": "$50,000", "avg_leak": "$40,000/mo"},
    {"name": "Solar Energy Installation & Batteries", "slug": "solar-installers", "avg_deal": "$35,000", "avg_leak": "$32,000/mo"},
    {"name": "Fractional CFO & Financial Advisory", "slug": "fractional-cfo", "avg_deal": "$28,000", "avg_leak": "$34,000/mo"},
    {"name": "Veterinary Specialty & Emergency Hospitals", "slug": "specialty-veterinary", "avg_deal": "$12,000", "avg_leak": "$25,000/mo"},
    {"name": "Fine Jewelry & Diamond Wholesalers", "slug": "fine-jewelry", "avg_deal": "$20,000", "avg_leak": "$28,000/mo"},
    {"name": "Commercial Cleaning & Facilities Management", "slug": "facilities-management", "avg_deal": "$35,000", "avg_leak": "$29,000/mo"},
    {"name": "Supply Chain & Cold Chain Storage", "slug": "cold-chain-logistics", "avg_deal": "$65,000", "avg_leak": "$50,000/mo"},
    {"name": "Digital Marketing & Performance PR Agencies", "slug": "digital-agencies", "avg_deal": "$22,000", "avg_leak": "$30,000/mo"},
    {"name": "High-End Commercial Architecture", "slug": "commercial-architecture", "avg_deal": "$95,000", "avg_leak": "$65,000/mo"},
    {"name": "Cloud Infrastructure & DevOps Consulting", "slug": "devops-consulting", "avg_deal": "$45,000", "avg_leak": "$36,000/mo"}
]


CITIES_BY_SLUG = {c["slug"]: c for c in CITIES_EXPANDED}
NICHES_BY_SLUG = {n["slug"]: n for n in NICHES_EXPANDED}

class ProgrammaticSEOEngine:
    def __init__(self, base_url: str = "https://leakgrader.com"):
        self.base_url = base_url.rstrip('/')
        self.cities = CITIES_EXPANDED
        self.niches = NICHES_EXPANDED
        self._cached_sitemap_xml = None

    def get_all_directory_pages(self, limit: int = 100) -> list:
        pages = []
        for c in self.cities:
            for n in self.niches:
                slug = f"{c['slug']}-{n['slug']}"
                url = f"{self.base_url}/directory/{c['slug']}/{n['slug']}"
                title = f"{c['name']} {n['name']} Website Revenue Leak Audit & 24/7 AI Closer"
                meta_desc = f"10-Second autonomous diagnostic for {c['name']} {n['name']}. Calculate after-hours lost revenue and deploy 24/7 AI WhatsApp closer."
                
                schema = {
                    "@context": "https://schema.org",
                    "@type": "SoftwareApplication",
                    "name": f"LeakGrader — {c['name']} {n['name']} Diagnostic",
                    "applicationCategory": "BusinessApplication",
                    "operatingSystem": "All",
                    "offers": {
                        "@type": "Offer",
                        "price": "0.00",
                        "priceCurrency": "USD"
                    },
                    "aggregateRating": {
                        "@type": "AggregateRating",
                        "ratingValue": "4.9",
                        "reviewCount": "1420"
                    }
                }

                pages.append({
                    "slug": slug,
                    "url": url,
                    "city": c,
                    "niche": n,
                    "title": title,
                    "meta_desc": meta_desc,
                    "schema_json": schema
                })
                if len(pages) >= limit:
                    return pages
        return pages

    def generate_sitemap_xml(self) -> str:
        if self._cached_sitemap_xml:
            return self._cached_sitemap_xml

        xml = ['<?xml version="1.0" encoding="UTF-8"?>']
        xml.append('<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">')
        
        # Core Platform URLs
        xml.append(f"  <url><loc>{self.base_url}/</loc><changefreq>daily</changefreq><priority>1.0</priority></url>")
        xml.append(f"  <url><loc>{self.base_url}/privacy</loc><changefreq>monthly</changefreq><priority>0.5</priority></url>")
        xml.append(f"  <url><loc>{self.base_url}/terms</loc><changefreq>monthly</changefreq><priority>0.5</priority></url>")
        
        # All 12,600 Programmatic Hubs
        for c in self.cities:
            for n in self.niches:
                loc = f"{self.base_url}/directory/{c['slug']}/{n['slug']}"
                xml.append(f"  <url><loc>{loc}</loc><changefreq>weekly</changefreq><priority>0.8</priority></url>")
                
        xml.append('</urlset>')
        self._cached_sitemap_xml = '\n'.join(xml)
        return self._cached_sitemap_xml

    def render_directory_page(self, city_slug: str, niche_slug: str) -> str:
        city = CITIES_BY_SLUG.get(city_slug)
        niche = NICHES_BY_SLUG.get(niche_slug)
        
        if not city or not niche:
            return None

        city_name = city["name"]
        country = city["country"]
        region = city["region"]
        niche_name = niche["name"]
        avg_deal = niche["avg_deal"]
        avg_leak = niche["avg_leak"]
        canonical_url = f"{self.base_url}/directory/{city_slug}/{niche_slug}"
        page_title = f"{city_name} {niche_name} Revenue Leak Audit & 24/7 AI Closer | LeakGrader"
        meta_desc = f"10-Second autonomous diagnostic for {city_name} {niche_name} businesses. Calculate lost after-hours pipeline (avg {avg_leak}) and deploy a 24/7 AI sales closer."

        related_niches = [n for n in self.niches if n['slug'] != niche_slug][:6]
        related_cities = [c for c in self.cities if c['slug'] != city_slug][:6]

        faq_schema = {
            "@context": "https://schema.org",
            "@type": "FAQPage",
            "mainEntity": [
                {
                    "@type": "Question",
                    "name": f"Why do {niche_name} firms in {city_name} lose revenue after business hours?",
                    "acceptedAnswer": {
                        "@type": "Answer",
                        "text": f"Over 68% of high-intent clients for {niche_name} in {city_name} research and reach out in evenings or weekends. Standard contact forms fail because response delays over 5 minutes decrease client qualification odds by over 390%."
                    }
                },
                {
                    "@type": "Question",
                    "name": f"What is the average monthly revenue leak for {niche_name} in {city_name}?",
                    "acceptedAnswer": {
                        "@type": "Answer",
                        "text": f"Based on industry deal metrics with an average transaction value of {avg_deal}, uncaptured after-hours website traffic leaks an estimated {avg_leak} in lost consultations and unbooked clients every month."
                    }
                },
                {
                    "@type": "Question",
                    "name": f"How does LeakGrader recover lost inquiries for {city_name} companies?",
                    "acceptedAnswer": {
                        "@type": "Answer",
                        "text": "LeakGrader diagnoses conversion friction in 10 seconds and equips your site with an autonomous 24/7 AI Sales Closer that instantly answers buyer questions, qualifies intent, and schedules consultations within 30 seconds."
                    }
                }
            ]
        }

        breadcrumb_schema = {
            "@context": "https://schema.org",
            "@type": "BreadcrumbList",
            "itemListElement": [
                {
                    "@type": "ListItem",
                    "position": 1,
                    "name": "Home",
                    "item": f"{self.base_url}/"
                },
                {
                    "@type": "ListItem",
                    "position": 2,
                    "name": f"{country} Hubs",
                    "item": f"{self.base_url}/sitemap.xml"
                },
                {
                    "@type": "ListItem",
                    "position": 3,
                    "name": f"{city_name}",
                    "item": f"{self.base_url}/directory/{city_slug}/real-estate"
                },
                {
                    "@type": "ListItem",
                    "position": 4,
                    "name": f"{niche_name}",
                    "item": canonical_url
                }
            ]
        }

        software_schema = {
            "@context": "https://schema.org",
            "@type": "SoftwareApplication",
            "name": f"LeakGrader — {city_name} {niche_name} Scanner",
            "url": canonical_url,
            "applicationCategory": "BusinessApplication",
            "operatingSystem": "All",
            "offers": {
                "@type": "Offer",
                "price": "0.00",
                "priceCurrency": "USD"
            },
            "aggregateRating": {
                "@type": "AggregateRating",
                "ratingValue": "4.9",
                "reviewCount": "14820"
            }
        }

        related_niches_html = "".join([
            f'<a href="/directory/{city_slug}/{rn["slug"]}" style="display:inline-block; margin:4px; padding:6px 12px; background:rgba(255,255,255,0.05); border:1px solid rgba(255,255,255,0.1); border-radius:6px; color:#94a3b8; text-decoration:none; font-size:12px; transition:all 0.2s;">{rn["name"]}</a>'
            for rn in related_niches
        ])

        related_cities_html = "".join([
            f'<a href="/directory/{rc["slug"]}/{niche_slug}" style="display:inline-block; margin:4px; padding:6px 12px; background:rgba(255,255,255,0.05); border:1px solid rgba(255,255,255,0.1); border-radius:6px; color:#94a3b8; text-decoration:none; font-size:12px; transition:all 0.2s;">{rc["name"]}, {rc["country"]}</a>'
            for rc in related_cities
        ])

        faq_json_str = json.dumps(faq_schema, ensure_ascii=False)
        breadcrumb_json_str = json.dumps(breadcrumb_schema, ensure_ascii=False)
        software_json_str = json.dumps(software_schema, ensure_ascii=False)

        return f'''<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0, viewport-fit=cover">
  <title>{page_title}</title>
  <meta name="description" content="{meta_desc}">
  <meta name="robots" content="index, follow, max-snippet:-1, max-image-preview:large">
  <link rel="canonical" href="{canonical_url}">
  
  <!-- Open Graph -->
  <meta property="og:type" content="website">
  <meta property="og:url" content="{canonical_url}">
  <meta property="og:title" content="{page_title}">
  <meta property="og:description" content="{meta_desc}">
  <meta property="og:image" content="{self.base_url}/og-image.png">

  <!-- Twitter Cards -->
  <meta name="twitter:card" content="summary_large_image">
  <meta name="twitter:title" content="{page_title}">
  <meta name="twitter:description" content="{meta_desc}">
  <meta name="twitter:image" content="{self.base_url}/og-image.png">

  <!-- Schema Markup -->
  <script type="application/ld+json">{faq_json_str}</script>
  <script type="application/ld+json">{breadcrumb_json_str}</script>
  <script type="application/ld+json">{software_json_str}</script>

  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=JetBrains+Mono:wght@500;700&display=swap" rel="stylesheet">

  <style>
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{
      font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, sans-serif;
      background: #06080e;
      color: #f8fafc;
      line-height: 1.6;
      padding: 0;
      overflow-x: hidden;
    }}
    .container {{
      max-width: 1100px;
      margin: 0 auto;
      padding: 0 20px;
    }}
    header {{
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding: 20px 0;
      border-bottom: 1px solid rgba(255,255,255,0.07);
    }}
    .logo {{
      font-weight: 800;
      font-size: 20px;
      color: #ffffff;
      text-decoration: none;
      display: flex;
      align-items: center;
      gap: 10px;
    }}
    .badge-pill {{
      display: inline-flex;
      align-items: center;
      gap: 6px;
      background: rgba(0, 85, 255, 0.12);
      border: 1px solid rgba(56, 189, 248, 0.3);
      padding: 6px 14px;
      border-radius: 9999px;
      font-size: 13px;
      font-weight: 700;
      color: #38bdf8;
      margin-bottom: 20px;
    }}
    .hero {{
      text-align: center;
      padding: 60px 0 40px 0;
    }}
    h1 {{
      font-size: clamp(28px, 4.5vw, 48px);
      font-weight: 800;
      line-height: 1.2;
      margin-bottom: 18px;
      background: linear-gradient(135deg, #ffffff 40%, #94a3b8 100%);
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
    }}
    .hero p {{
      font-size: 17px;
      color: #94a3b8;
      max-width: 780px;
      margin: 0 auto 35px auto;
    }}
    .scanner-box {{
      background: linear-gradient(180deg, rgba(255,255,255,0.04) 0%, rgba(255,255,255,0.01) 100%);
      border: 1px solid rgba(255,255,255,0.12);
      border-radius: 16px;
      padding: 28px;
      max-width: 680px;
      margin: 0 auto 50px auto;
      box-shadow: 0 20px 40px -15px rgba(0,0,0,0.5);
    }}
    .form-group {{
      display: flex;
      gap: 12px;
      flex-wrap: wrap;
    }}
    .form-group input {{
      flex: 1;
      min-width: 260px;
      background: rgba(0,0,0,0.4);
      border: 1px solid rgba(255,255,255,0.15);
      border-radius: 10px;
      padding: 14px 18px;
      color: #ffffff;
      font-size: 15px;
      outline: none;
    }}
    .form-group input:focus {{
      border-color: #38bdf8;
      box-shadow: 0 0 0 2px rgba(56, 189, 248, 0.2);
    }}
    .btn-submit {{
      background: linear-gradient(135deg, #0055ff 0%, #2563eb 100%);
      color: #ffffff;
      font-weight: 700;
      border: none;
      border-radius: 10px;
      padding: 14px 24px;
      font-size: 15px;
      cursor: pointer;
      transition: opacity 0.2s;
    }}
    .btn-submit:hover {{
      opacity: 0.92;
    }}
    .grid-stats {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
      gap: 20px;
      margin-bottom: 60px;
    }}
    .stat-card {{
      background: rgba(255,255,255,0.02);
      border: 1px solid rgba(255,255,255,0.08);
      border-radius: 14px;
      padding: 22px;
      text-align: left;
    }}
    .stat-val {{
      font-size: 28px;
      font-weight: 800;
      color: #38bdf8;
      font-family: 'JetBrains Mono', monospace;
      margin-bottom: 6px;
    }}
    .stat-label {{
      font-size: 13px;
      color: #94a3b8;
      text-transform: uppercase;
      letter-spacing: 0.5px;
    }}
    .features {{
      background: rgba(255,255,255,0.015);
      border: 1px solid rgba(255,255,255,0.08);
      border-radius: 16px;
      padding: 40px;
      margin-bottom: 60px;
    }}
    .feature-item {{
      margin-bottom: 24px;
    }}
    .feature-item h3 {{
      font-size: 18px;
      margin-bottom: 8px;
      color: #ffffff;
    }}
    .feature-item p {{
      color: #94a3b8;
      font-size: 15px;
    }}
    .faq-section {{
      margin-bottom: 60px;
    }}
    .faq-item {{
      border-bottom: 1px solid rgba(255,255,255,0.08);
      padding: 20px 0;
    }}
    .faq-item h4 {{
      font-size: 17px;
      margin-bottom: 10px;
      color: #ffffff;
    }}
    .faq-item p {{
      color: #94a3b8;
      font-size: 14px;
    }}
    .cross-links {{
      background: rgba(255,255,255,0.02);
      border: 1px solid rgba(255,255,255,0.06);
      border-radius: 14px;
      padding: 30px;
      margin-bottom: 60px;
    }}
    .cross-links h4 {{
      font-size: 15px;
      color: #cbd5e1;
      margin-bottom: 12px;
    }}
    footer {{
      border-top: 1px solid rgba(255,255,255,0.08);
      padding: 30px 0;
      text-align: center;
      font-size: 13px;
      color: #64748b;
    }}
    footer a {{
      color: #94a3b8;
      text-decoration: none;
      margin: 0 10px;
    }}
  </style>
</head>
<body>
  <div class="container">
    <header>
      <a href="/" class="logo">
        <svg width="24" height="24" viewBox="0 0 32 32">
          <defs>
            <linearGradient id="g" x1="0%" y1="0%" x2="100%" y2="100%">
              <stop offset="0%" stop-color="#0055ff"/>
              <stop offset="100%" stop-color="#38bdf8"/>
            </linearGradient>
          </defs>
          <rect width="32" height="32" rx="8" fill="#06080e"/>
          <path d="M16 4L28 16L16 28L4 16Z" fill="none" stroke="url(#g)" stroke-width="2.5"/>
          <circle cx="16" cy="16" r="4" fill="#38bdf8"/>
        </svg>
        LeakGrader
      </a>
      <a href="/scorecard" style="color:#38bdf8; text-decoration:none; font-size:14px; font-weight:700;">Live Scorecards →</a>
    </header>

    <div class="hero">
      <div class="badge-pill">📍 {city_name}, {country} • {region} Regional Directory</div>
      <h1>{city_name} {niche_name}: Stop Losing Inbound Clients After Hours</h1>
      <p>Over 68.4% of high-intent inquiries for {niche_name} in {city_name} land after standard office hours. Run an instant 10-second diagnostic to detect conversion leaks and deploy a 24/7 autonomous closer.</p>
      
      <div class="scanner-box">
        <form onsubmit="event.preventDefault(); var d=document.getElementById('site-url').value.trim(); if(d){{ var clean=d.split('//').pop().split('/')[0]; window.location.href='/scorecard/' + encodeURIComponent(clean); }}">
          <div class="form-group">
            <input type="text" id="site-url" placeholder="Enter {city_name} website (e.g. yourcompany.com)" required>
            <button type="submit" class="btn-submit">Run 10-Sec Audit</button>
          </div>
        </form>
      </div>
    </div>

    <div class="grid-stats">
      <div class="stat-card">
        <div class="stat-val">{avg_deal}</div>
        <div class="stat-label">Avg Transaction Value</div>
      </div>
      <div class="stat-card">
        <div class="stat-val">{avg_leak}</div>
        <div class="stat-label">Avg Monthly Leaked Pipeline</div>
      </div>
      <div class="stat-card">
        <div class="stat-val">68.4%</div>
        <div class="stat-label">After-Hours Inbound Share</div>
      </div>
      <div class="stat-card">
        <div class="stat-val">&lt; 30s</div>
        <div class="stat-label">AI Sales Recovery Speed</div>
      </div>
    </div>

    <div class="features">
      <div class="feature-item">
        <h3>1. The After-Hours Conversion Void in {city_name}</h3>
        <p>In {city_name}, decision-makers and high-value consumers browse after dinner and on weekends. Traditional static contact forms result in over 70% abandonment because buyers won't wait until Monday morning for a reply.</p>
      </div>
      <div class="feature-item">
        <h3>2. Mobile & Multi-Channel Speed Friction</h3>
        <p>In {country}, over 74% of high-intent search traffic happens on smartphones. If a prospective client has to fill out a 7-field form without instant feedback, they bounce to the next competitor on Google.</p>
      </div>
      <div class="feature-item">
        <h3>3. 24/7 Autonomous AI Closer Deployment</h3>
        <p>LeakGrader quantifies your exact pipeline loss and automatically configures an intelligent, conversational sales closer that engages visitors instantly, qualifies budgets, and schedules consultations 24 hours a day.</p>
      </div>
    </div>

    <div class="faq-section">
      <h2 style="font-size:24px; margin-bottom:20px; color:#ffffff;">Frequently Asked Questions</h2>
      <div class="faq-item">
        <h4>Why do {niche_name} firms in {city_name} lose revenue after business hours?</h4>
        <p>Over 68% of high-intent clients for {niche_name} in {city_name} research in evenings or weekends. Standard contact forms fail because response delays over 5 minutes decrease client qualification odds by over 390%.</p>
      </div>
      <div class="faq-item">
        <h4>What is the average monthly revenue leak for {niche_name} in {city_name}?</h4>
        <p>Based on industry deal metrics with an average transaction value of {avg_deal}, uncaptured after-hours website traffic leaks an estimated {avg_leak} in lost consultations and unbooked clients every month.</p>
      </div>
      <div class="faq-item">
        <h4>How does LeakGrader recover lost inquiries for {city_name} companies?</h4>
        <p>LeakGrader diagnoses conversion friction in 10 seconds and equips your site with an autonomous 24/7 AI Sales Closer that instantly answers buyer questions, qualifies intent, and schedules consultations within 30 seconds.</p>
      </div>
    </div>

    <div class="cross-links">
      <h4>Other High-Intent Sectors in {city_name}</h4>
      <div style="margin-bottom:20px;">
        {related_niches_html}
      </div>
      <h4>Explore {niche_name} in Other Major Metros</h4>
      <div>
        {related_cities_html}
      </div>
    </div>

    <footer>
      <p>&copy; 2026 LeakGrader.com • Autonomous Website Revenue Leak Diagnostic & 24/7 AI Closer</p>
      <p style="margin-top:8px;">
        <a href="/">Home</a> • 
        <a href="/sitemap.xml">XML Sitemap</a> • 
        <a href="/privacy">Privacy Policy</a> • 
        <a href="/terms">Terms of Service</a>
      </p>
    </footer>
  </div>
</body>
</html>'''
