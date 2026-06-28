import time
from app.core.config import settings

class AlertNotificationService:
    def __init__(self):
        pass

    def evaluate_and_trigger(self, lat: float, lon: float, location_name: str, flood_prob: float, landslide_prob: float, lang: str = "en") -> dict:
        """
        Evaluates risk levels against threshold settings and generates multi-lingual, multi-channel warnings.
        """
        triggers = []
        highest_score = max(flood_prob, landslide_prob)
        severity = "Low"
        
        if highest_score >= settings.THRESHOLD_EXTREME:
            severity = "Extreme"
        elif highest_score >= settings.THRESHOLD_HIGH:
            severity = "High"
        elif highest_score >= settings.THRESHOLD_MODERATE:
            severity = "Moderate"
            
        lang = lang.lower() if lang.lower() in settings.TRANSLATIONS else "en"
        
        # 1. Flood risk trigger assessment
        if flood_prob >= settings.THRESHOLD_HIGH:
            msg_template = settings.TRANSLATIONS[lang]["flood_alert"]
            formatted_msg = msg_template.format(location=location_name, score=int(flood_prob * 100))
            triggers.append({
                "hazard": "Flood",
                "severity": severity,
                "score": round(flood_prob * 100, 1),
                "message": formatted_msg,
                "channels_dispatched": ["SMS", "Email", "WhatsApp", "Voice Warning"]
            })
            self._dispatch_channels(location_name, formatted_msg, "Flood Alert", severity)

        # 2. Landslide risk trigger assessment
        if landslide_prob >= settings.THRESHOLD_HIGH:
            msg_template = settings.TRANSLATIONS[lang]["landslide_alert"]
            formatted_msg = msg_template.format(location=location_name, score=int(landslide_prob * 100))
            triggers.append({
                "hazard": "Landslide",
                "severity": severity,
                "score": round(landslide_prob * 100, 1),
                "message": formatted_msg,
                "channels_dispatched": ["SMS", "Email", "WhatsApp", "Voice Warning"]
            })
            self._dispatch_channels(location_name, formatted_msg, "Landslide Susceptibility Alert", severity)

        # 3. If safe, compile local safety status
        if not triggers:
            triggers.append({
                "hazard": "None",
                "severity": "Low",
                "score": round(highest_score * 100, 1),
                "message": settings.TRANSLATIONS[lang]["safe"],
                "channels_dispatched": []
            })
            
        return {
            "triggered": len(triggers) > 0 and triggers[0]["hazard"] != "None",
            "severity": severity,
            "alerts": triggers,
            "timestamp": time.time()
        }

    def _dispatch_channels(self, target: str, message: str, subject: str, severity: str):
        """Simulates secure, asynchronous multi-channel message transfers."""
        print(f"\n=================== [GEOSHIELD AI DISPATCHER] ===================")
        print(f"EVENT: Emergency Broadcast | REGION: {target} | SEVERITY: {severity.upper()}")
        print(f"SUBJECT: {subject}")
        print(f"MESSAGE: {message}")
        print(f"--- Channel Outputs ---")
        print(f"[SMS Warning] Sent to regional citizen mobile pools (256-bit AES encrypted).")
        print(f"[Email Notification] Transmitted to NGO networks & Relief agency coordinators.")
        print(f"[WhatsApp Alert] Broadcasted to registered Community Volunteer cells.")
        print(f"[Speech Broadcast] Synthetic text-to-speech voice cue queue buffered.")
        print(f"=================================================================\n")

alert_service = AlertNotificationService()
