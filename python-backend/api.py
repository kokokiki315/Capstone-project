import os
import google.generativeai as genai
import PIL.Image
from db import storeevent
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure the official Google API
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

def geminiApi(filename):
    content = "API_ERROR"
    
    # Prompt for your automation logic
    prompt_text = (
        "Analyze this security camera image and classify the situation:\n"
        "1. If you see a delivery courier or someone holding a package, say 'ALERT: DELIVERY'.\n"
        "2. If you see a normal visitor standing at the gate, say 'ALERT: VISITOR'.\n"
        "3. If you see someone loitering, wearing a mask, climbing, or stealing, say 'ALERT: SUSPICIOUS'.\n"
        "Otherwise, briefly describe the scene."
    )
    
    try:
        api_key = os.getenv("GOOGLE_API_KEY")
        print(f"DEBUG: Loaded API Key: {api_key[:5]}..." if api_key else "DEBUG: NO API KEY FOUND")       
        # 1. Load the Model
        model = genai.GenerativeModel('gemini-2.5-flash-lite')

        # 2. Load the Image directly (No complex Base64 needed!)
        img = PIL.Image.open(filename)

        # 3. Send Request
        response = model.generate_content([prompt_text, img])
        
        # 4. Get Text
        content = response.text.strip()
        print("GOOGLE API SUCCESS:", content)

    except Exception as e:
        print("GOOGLE API EXCEPTION:", e)
        content = "System Error"

    finally:
        # 5. Save to DB and Return
        storeevent(os.path.basename(filename), content)
        return content