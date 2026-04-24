import os
from fastapi.responses import FileResponse
import uuid
from fastapi import FastAPI, Request, HTTPException, Form
from pydantic import BaseModel
import paho.mqtt.client as mqtt
import requests

app = FastAPI()
# --- USER DATABASE (Temporary) ---
# In a real app, you'd use a database like SQLite or PostgreSQL
# Update your users_db at the top of flow.py
users_db = {
    "0712345678": {
        "password": "1234", 
        "name": "Muslimu", 
        "balance": 0.00,  # Starting units in kWh
        "meter_ids": ["14205678112"]
    }
}
from fastapi.responses import FileResponse

@app.get("/")
async def get_login():
    return FileResponse("login.html")

# Create a temporary storage for the currently logged-in user
# (Normally, we would use proper "sessions" or "cookies" here)
current_user = {"username": "Mteja"}

@app.get("/dashboard")
async def get_dashboard():
    # Make sure we only show the dashboard if someone has logged in
    # (Simplified login check for this demo)
    return FileResponse("index.html")

# NEW ENDPOINT: Let the browser ask "who is logged in?"
# Update Line 30-32 in flow.py
@app.get("/api/user_data")
async def provide_user_data():
    phone = current_user["username"]
    user_info = users_db.get(phone, {"balance": 0.00})
    return {
        "username": phone,
        "balance": user_info.get("balance", 0.00)
    }

# This acts as your temporary database
users_db = {
    "0712345678": {"password": "1234", "name": "Mteja"}
}

@app.post("/login")
async def login_check(data: dict):
    username = data.get("username")
    password = data.get("password")

    # Check if the number exists in our "database"
    if username in users_db:
        if users_db[username]["password"] == password:
            # Update the global current_user for the dashboard to see
            global current_user
            current_user["username"] = users_db[username]["name"]
            return {"status": "success"}
        else:
            return {"status": "error", "message": "Nenosiri si sahihi!"}
    else:
        # If number is not found, the frontend will redirect to registration
        return {"status": "not_found"}
class UserLogin(BaseModel):
    username: str
    password: str
@app.get("/register")
async def get_register():
    return FileResponse("register.html")
# For the Payment page
@app.get("/payment")
async def get_payment():
    return FileResponse("payment.html")

# For the History page
@app.get("/history")
async def get_history():
    return FileResponse("history.html")
class UserRegister(BaseModel):
    username: str
    password: str
    meter_ids: list = {}  # Landlord support: list of meters
class NewMeter(BaseModel):
    username: str  # To know which account to add the meter to
    nickname: str
    meter_number: str
    # Temporary store for transactions
history_db = [
    {"date": "2026-04-10", "nickname": "Home", "amount": "5,000", "token": "4421-9908-1123-4456-0091"},
]
from fastapi.responses import FileResponse

# THIS IS THE "FRONT DOOR"
# It now points directly to your login page
@app.get("/")
async def get_login():
    return FileResponse("login.html")

# YOUR DASHBOARD IS NOW HERE
@app.get("/dashboard")
async def get_dashboard():
    return FileResponse("index.html")
@app.get("/history")
async def get_history():
    return FileResponse("history.html")

# Route to get history data as JSON
@app.get("/api/history")
async def get_history_data():
    return history_db
@app.post("/register")
async def register(user: UserRegister):
    # 1. Check if user already exists
    if user.username in users_db:
        return {"status": "error", "message": "Namba hii tayari imesajiliwa!"}
    
    # 2. Add to your dictionary database
    users_db[user.username] = {
        "password": user.password,
        "meter_ids": user.meter_ids if user.meter_ids else []
    }
    
    # 3. Effectively log them in
    current_user["username"] = user.username
    
    return {"status": "success", "message": "Account created successfully"}

@app.post("/login")
async def login(user: UserLogin):
    # Check if user exists AND password matches
    if user.username in users_db and users_db[user.username]["password"] == user.password:
        return {"status": "success"}
    else:
        return {"status": "error", "message": "User not found"}
@app.get("/logout")
async def logout():
    global current_user
    current_user = {"username": None} # Clear the session
    return FileResponse("login.html")
@app.post("/add_meter")
async def add_meter(meter: NewMeter):
    if meter.username in users_db:
        # Tanzanian meters are usually 11 digits
        if len(meter.meter_number) != 11:
            return {"status": "error", "message": "Namba ya mita lazima iwe na tarakimu 11"}
        
        users_db[meter.username]["meter_ids"].append(meter.meter_number)
        return {"status": "success", "message": "Mita imeongezwa!"}
    
    return {"status": "error", "message": "Mtumiaji hajapatikana"}
# --- UPDATED USER DATABASE LOGIC ---
users_db = {
    "mofaza": {
        "password": "123",
        "meters": {
            "Home": "2421000001",
            "Apartment 1": "2421000002",
            "Office": "2421000003"
        }
    }
}

@app.post("/add_meter")
async def add_meter(username: str, nickname: str, meter_number: str):
    if username in users_db:
        users_db[username]["meters"][nickname] = meter_number
        return {"status": "success", "message": f"Added {nickname}"}
    return {"status": "error", "message": "User not found"}
class Feedback(BaseModel):
    issue_type: str
    message: str
    timestamp: str

@app.post("/feedback")
async def receive_feedback(fb: Feedback):
    # In a real app, you would send this to your email or a database
    print(f"NEW FEEDBACK: [{fb.issue_type}] {fb.message} at {fb.timestamp}")
    
    # Simulating a successful save
    return {"status": "success", "message": "Feedback received"}
# --- MQTT CONFIGURATION ---
MQTT_BROKER = "mqtt-dashboard.com"
MQTT_PORT = 1883
AZAMPAY_TOKEN = "TEST_TOKEN"
AZAMPAY_URL = "https://sandbox.azampay.co.tz"

# --- MQTT LOGIC ---
# This is the version update I mentioned:
# Use the ClientID from your HiveMQ dashboard
client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id="clientId-PhYHy5Rj4f")
client.connect(MQTT_BROKER, MQTT_PORT, 60)

# This finds the folder where flow.py is sitting
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
@app.get("/dashboard")
async def get_dashboard():
    return FileResponse("dashboard.html")
@app.get("/")
async def read_index():
    # This looks for index.html in the same folder as flow.py
    path = os.path.join(BASE_DIR, "index.html")
    if os.path.exists(path):
        return FileResponse(path)
    return {"error": "index.html not found in main folder"}
@app.get("/payment")
async def get_payment_page():
    return FileResponse("payment.html")
@app.post("/pay")
async def initiate_payment(meter_number: str, amount: float, phone: str, provider: str):
    # This sends a placeholder message so you can see it on HiveMQ immediately
    send_token_to_meter(meter_number, f"PENDING_FOR_{amount}")
    
    payload = {
        "accountNumber": phone,
        "amount": str(amount),
        "currency": "TZS",
        "externalId": f"LUKU_{meter_number}_{uuid.uuid4().hex[:6]}",
        "provider": provider
    }
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {AZAMPAY_TOKEN}"
    }
    
    try:
        response = requests.post(AZAMPAY_URL, json=payload, headers=headers)
        return response.json()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
@app.post("/api/buy_units")
async def buy_units(data: dict):
    global current_user
    phone = current_user.get("username")
    amount = float(data.get("amount", 0))
    
    if phone in users_db:
        # Conversion logic: 1 kWh = TSH 350 (Example rate)
        new_units = round(amount / 350, 2)
        users_db[phone]["balance"] += new_units
        
        return {
            "status": "success", 
            "new_balance": users_db[phone]["balance"],
            "added": new_units
        }
    return {"status": "error", "message": "User not logged in"}
@app.get("/manifest.json")
async def get_manifest():
    paths = [
        os.path.join(BASE_DIR, "manifest.json"),
        os.path.join(BASE_DIR, "static", "manifest.json")
    ]
    for path in paths:
        if os.path.exists(path):
            return FileResponse(path)
    return {"error": "manifest.json not found"}

def send_token_to_meter(meter_id, token):
    # This creates the path: luku/meter/123456
    topic = f"luku/meter/{meter_id}"
    
    # This actually pushes the token to HiveMQ
    result = client.publish(topic, token)
    
    # rc == 0 means "Return Code: Success"
    return result.rc == 0
@app.post("/callback")
async def payment_callback(request: Request):
    data = await request.json()
    
    if data.get("transactionstatus") == "success":
        luku_token = data.get("utilityref", "NO_TOKEN_FOUND")
        # Extract meter_id from the externalId (LUKU_12345_abc)
        external_id = data.get("externalId", "")
        meter_id = external_id.split("_")[1] if "_" in external_id else "unknown"
        
        # Send the REAL token to the ESP32
        # Ensure this line exists in your /callback or /pay route:
        mqtt_success = send_token_to_meter(meter_id, luku_token)
        print(f"MQTT Publish Status: {mqtt_success}")
        if mqtt_success:
            return {"status": "success", "token_sent": True, "token": luku_token}
        else:
            return {"status": "error", "message": "Failed to send token to HiveMQ"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
    