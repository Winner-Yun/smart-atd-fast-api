import os

from dotenv import load_dotenv
from fastapi import FastAPI

from src.controllers.auth import auth_router
from src.controllers.workspaces import workspace_router
from src.controllers.invite import invite_router
from src.controllers.face_embedding import face_router
from src.controllers.health import health_router
from src.controllers.leave import leave_router
from src.controllers.attendance import attendance_router
from src.controllers.notification import notification_router
from src.controllers.chat import chat_router
load_dotenv()

app_env = os.getenv('APP_ENV', 'local')

app = FastAPI(
    title='Smart ATD Backend',
    version='1.0.0',
    description='API endpoints for Smart ATD Backend',
    docs_url='/smart-docs' if app_env == 'local' else None,
    redoc_url='/smart-redoc' if app_env == 'local' else None,
)


app.include_router(auth_router, prefix='/auth')
app.include_router(workspace_router, prefix='/workspace')
app.include_router(invite_router, prefix='/invite')
app.include_router(face_router, prefix='/face')
app.include_router(leave_router, prefix='/leave')
app.include_router(attendance_router, prefix='/attendance')
app.include_router(notification_router, prefix='/notification')
app.include_router(chat_router, prefix='/chat')
app.include_router(health_router, prefix='/health')
