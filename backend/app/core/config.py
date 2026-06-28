import os
from typing import Dict, Any


class Settings:
    PROJECT_NAME: str = "GeoShield AI"
    VERSION: str = "1.0.0"
    API_PREFIX: str = "/api"
    
    # Security
    SECRET_KEY: str = os.getenv("JWT_SECRET", "4749f7b13a36db5ee00388f6b9c9f7fe7e61e0bbcd33f81e6dc8b09339e14a1a")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440  # 24 hours
    
    # DB (Dual-Mode: Auto-fallbacks to SQLite if Postgres string is absent/unreachable)
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./geoshield.db")
    
    # External APIs
    OPENWEATHER_API_KEY: str = os.getenv("OPENWEATHER_API_KEY", "mock_weather_key_geoshield")
    GEE_PROJECT: str = os.getenv("GEE_PROJECT", "mock-gee-project")
    
    # Threat Alerts Thresholds
    THRESHOLD_EXTREME: float = 0.75
    THRESHOLD_HIGH: float = 0.50
    THRESHOLD_MODERATE: float = 0.25
    
    # Multi-language translations for critical alerts and safety instructions (EN, HI, MR)
    TRANSLATIONS: Dict[str, Dict[str, str]] = {
        "en": {
            "flood_alert": "CRITICAL: High flood risk predicted at {location}. Risk Score: {score}%. Prepare to evacuate to high elevation immediately.",
            "landslide_alert": "CRITICAL: Landslide susceptibility alert at {location}. Risk Score: {score}%. Check terrain slopes and avoid hillsides.",
            "safe": "No active warnings for your coordinate grid. Local slope and water indices are stable.",
            "sos_dispatched": "SOS Alert Received! Rescue Volunteer {name} (Skill: {skill}) has been dispatched with vehicle {vehicle}. Meet them at designated safe point.",
            "chatbot_welcome": "Hello, I am the GeoShield AI Copilot. Ask me about real-time hazards, nearest shelters, or evacuation routing.",
            "evac_route_tip": "Recommended Evacuation Path: Bypassing active flood zones and high-slope terrains. Head to the nearest shelter at {shelter}."
        },
        "hi": {
            "flood_alert": "गंभीर चेतावनी: {location} पर भारी बाढ़ का खतरा है। खतरा स्कोर: {score}%। तुरंत ऊंचाई वाले सुरक्षित क्षेत्रों में जाने की तैयारी करें।",
            "landslide_alert": "गंभीर चेतावनी: {location} पर भूस्खलन का खतरा है। खतरा स्कोर: {score}%। पहाड़ी ढलानों से दूर रहें।",
            "safe": "आपके ग्रिड के लिए कोई सक्रिय चेतावनी नहीं है। स्थानीय ढलान और जल सूचकांक स्थिर हैं।",
            "sos_dispatched": "एसओएस अनुरोध प्राप्त हुआ! बचाव स्वयंसेवक {name} ({skill}) वाहन {vehicle} के साथ रवाना हो चुके हैं। सुरक्षित बिंदु पर मिलें।",
            "chatbot_welcome": "नमस्ते, मैं जियोशील्ड एआई कोपायलट हूं। मुझसे आपदाओं, निकटतम आश्रयों या बचाव मार्गों के बारे में पूछें।",
            "evac_route_tip": "अनुशंसित निकासी मार्ग: सक्रिय बाढ़ क्षेत्रों और तीव्र पहाड़ी ढलानों को छोड़कर। {shelter} पर निकटतम राहत शिविर की ओर बढ़ें।"
        },
        "mr": {
            "flood_alert": "अतिदक्षतेचा इशारा: {location} येथे पुराचा मोठा धोका वर्तवण्यात आला आहे. धोका पातळी: {score}%. त्वरित उंच ठिकाणी सुरक्षित स्थलांतर करा.",
            "landslide_alert": "अतिदक्षतेचा इशारा: {location} येथे दरड कोसळण्याचा धोका आहे. धोका पातळी: {score}%. डोंगराळ उतारांवर जाणे टाळा.",
            "safe": "तुमच्या क्षेत्रासाठी कोणतीही सक्रिय धोक्याची सूचना नाही. स्थानिक डोंगरउतार आणि जल पातळी स्थिर आहे.",
            "sos_dispatched": "एसओएस अलर्ट प्राप्त झाला! बचाव स्वयंसेवक {name} ({skill}) वाहन {vehicle} सह रवाना झाले आहेत. सुरक्षित ठिकाणी त्यांची भेट घ्या.",
            "chatbot_welcome": "नमस्कार, मी जिओशील्ड एआई कोपायलट आहे. मला रिअल-टाइम धोके, जवळील निवारे किंवा सुरक्षित स्थलांतर मार्गांबद्दल विचारा.",
            "evac_route_tip": "शिफारस केलेला स्थलांतर मार्ग: पूरग्रस्त भाग आणि तीव्र डोंगरउतार वगळून. {shelter} जवळील निवाऱ्याकडे प्रस्थान करा।"
        }
    }

settings = Settings()
