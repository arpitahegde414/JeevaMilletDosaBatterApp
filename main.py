from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from firebase_admin import credentials, firestore, initialize_app
from datetime import datetime, timedelta
import re
from starlette.middleware.sessions import SessionMiddleware
from auth import router as auth_router

app = FastAPI()
app.include_router(auth_router)
app.add_middleware(SessionMiddleware, secret_key="your-secret-key")
templates = Jinja2Templates(directory="templates")

# Initialize Firebase
cred = credentials.Certificate("firebase_service.json")
initialize_app(cred)
db = firestore.client()

# Utility function to get active notices
def get_active_notices():
    notices_ref = db.collection("notices")
    active_notices = notices_ref.where("active_status", "==", True).stream()
    return [notice.to_dict()["notice_text"] for notice in active_notices]

@app.get("/", response_class=HTMLResponse)
async def read_form(request: Request):
    notices = get_active_notices()
    return templates.TemplateResponse("index.html", {
        "request": request,
        "notices": notices,
        "now": datetime.now(),
        "timedelta": timedelta
    })

@app.post("/order")
async def place_order(
    request: Request,
    username: str = Form(...),
    phone: str = Form(...),
    order_date: str = Form(...),
    batter_type: str = Form(...),
    quantity: str = Form(...)
):
    errors = []
    # Validate username and phone
    if not username.strip():
        errors.append("Username is required.")
    phone_pattern = re.compile(r"^\d{10}$")
    if not phone_pattern.match(phone):
        errors.append("Phone number must be a 10-digit number.")
    # Validate order date minimum 2 days ahead
    try:
        order_dt = datetime.strptime(order_date, "%Y-%m-%d")
        if order_dt < (datetime.now() + timedelta(days=2)).replace(hour=0,minute=0,second=0,microsecond=0):
            errors.append("Order date must be at least 2 days ahead.")
    except Exception:
        errors.append("Invalid date format. Use YYYY-MM-DD.")

    if not batter_type or batter_type not in ["Raagi Dosa Batter", "Foxtail Dosa Batter", "Jowar Dosa Batter"]:
            errors.append("Please select a valid dosa batter type.")
    if not quantity or quantity not in ["750 grams", "1 Kg", "1.5 Kg"]:
            errors.append("Please select a valid quantity.")

    if errors:
        notices = get_active_notices()
        return templates.TemplateResponse("index.html", {
            "request": request,
            "errors": errors,
            "notices": notices,
            "username": username,
            "phone": phone,
            "order_date": order_date,
            "quantity": quantity,
            "batter_type": batter_type,
            "now": datetime.now(),
            "timedelta": timedelta
        })
        
    # Save order to Firebase
    order_data = {
        "username": username.strip(),
        "phone": phone,
        "order_date": order_date,
        "quantity": quantity,
        "batter_type": batter_type,
        "timestamp": datetime.now().isoformat()
    }
    db.collection("orders").add(order_data)

    success_msg = "Order placed successfully for date: " + order_date
    notices = get_active_notices()
    return templates.TemplateResponse("index.html", {
        "request": request,
        "success_msg": success_msg,
        "notices": notices,
        "now": datetime.now(),
        "timedelta": timedelta
    })

