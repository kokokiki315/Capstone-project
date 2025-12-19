import os
import google.generativeai as genai
import PIL.Image
from db import storeevent
from dotenv import load_dotenv

load_dotenv()

# Configure API
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

def geminiApi(filename):
    content = "API_ERROR"
    
    # Standard prompt
    prompt_text = (
        "Analyze this security camera image and classify the situation:\n"
        "1. If you see a delivery courier or someone holding a package, say 'ALERT: DELIVERY'.\n"
        "2. If you see a normal visitor standing at the gate, say 'ALERT: VISITOR'.\n"
        "3. If you see someone loitering, wearing a mask, climbing, or stealing, say 'ALERT: SUSPICIOUS'.\n"
        "Otherwise, briefly describe the scene."
    )
    
    try:
        # --- FIX 1: Use the specific model version ---
        model = genai.GenerativeModel('gemini-1.5-flash-latest') 
        
        # --- FIX 2: Debug Print ---
        print(f"[DEBUG] Sending {filename} to Google AI...")
        
        img = PIL.Image.open(filename)
        response = model.generate_content([prompt_text, img])
        
        content = response.text.strip()
        print(f"[SUCCESS] AI Response: {content}")

    except Exception as e:
        # --- FIX 3: Print the ACTUAL error ---
        print(f"[CRITICAL ERROR] Google AI Failed: {e}")
        # Fallback: If Flash fails, try the older model just to test connection
        if "404" in str(e):
             print("[TIP] Try running: pip install -U google-generativeai")

    finally:
        try:
            storeevent(os.path.basename(filename), content)
        except Exception as db_e:
            print(f"[DB ERROR] Could not save to database: {db_e}")
            
        return content