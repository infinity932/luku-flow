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
users_db = {} 
from fastapi.responses import FileResponse

@app.get("/")
async def get_login():
    return FileResponse("login.html")

@app.get("/dashboard")
async def get_dashboard():
    return FileResponse("index.html")

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
    if user.username in users_db:
        return {"status": "error", "message": "User already exists!"}
    users_db[user.username] = {"password": user.password, "meters": user.meter_ids}
    return {"status": "success", "message": "Account created!"}

@app.post("/login")
async def login(username: str = Form(...), password: str = Form(...)):
    user = users_db.get(username)
    if user and user["password"] == password:
        return {"status": "success", "user": username}
    return {"status": "error", "message": "Invalid login"}
@app.get("/logout")
async def logout():
    # This sends the user back to the login page
    return FileResponse("login.html")
@app.post("/add_meter")
async def add_meter(meter: NewMeter):
    # Check if user exists in our dictionary
    if meter.username in users_db:
        # Tanzanian meters are 11 digits
        if len(meter.meter_number) != 11:
            return {"status": "error", "message": "Namba ya mita lazima iwe na namba 11"}
        
        # Add to the landlord's list
        users_db[meter.username]["meters"][meter.nickname] = meter.meter_number
        print(f"Added {meter.nickname} to {meter.username}")
        return {"status": "success", "message": "Mita imesajiliwa kikamilifu!"}
    
    return {"status": "error", "message": "User not found"}
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
    