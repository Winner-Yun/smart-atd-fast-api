import os

from dotenv import load_dotenv
from fastapi import FastAPI

from src.controllers.auth_controller import auth_router
from src.controllers.workspaces_controller import workspace_router
from src.controllers.invite_controller import invite_router
from src.controllers.face_embedding_controller import face_router
from src.controllers.health_controller import health_router
from src.controllers.leave_controller import leave_router
from src.controllers.attendance_controller import attendance_router
from src.controllers.notification_controller import notification_router
from src.controllers.chat_controller import chat_router
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
