from fastapi import APIRouter, Request
from starlette.config import Config
from starlette.middleware.sessions import SessionMiddleware
from authlib.integrations.starlette_client import OAuth, OAuthError
from fastapi.templating import Jinja2Templates
from starlette.config import Config
from datetime import datetime, timedelta

router = APIRouter()

config = Config("local.env")
client_id = config("GOOGLE_CLIENT_ID")
client_secret = config("GOOGLE_CLIENT_SECRET")
secret_key = config("SECRET_KEY")

oauth = OAuth(config)
oauth.register(
    name='google',
    client_id=client_id,
    client_secret=client_secret,
    server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
    client_kwargs={'scope': 'openid email profile'}
)

templates = Jinja2Templates(directory="templates")

@router.get("/login")
async def login(request: Request):
    redirect_uri = request.url_for('auth')
    return await oauth.google.authorize_redirect(request, redirect_uri)

@router.get("/auth")
async def auth(request: Request):
    try:
        token = await oauth.google.authorize_access_token(request)
        user = await oauth.google.userinfo(token=token)
    except OAuthError:
        return {"error": "Authentication failed"}
    request.session['user'] = {
        'username': user.get("name"),
        'email': user.get("email"),
        'sub': user.get('sub')
    }
    now = datetime.now()
    return templates.TemplateResponse("index.html", {
        "request": request,
        "user": request.session.get('user'),
        "now": now,
        "timedelta": timedelta
    })

@router.get("/logout")
async def logout(request: Request):
    request.session.pop('user', None)
    return {"message": "Logged out"}