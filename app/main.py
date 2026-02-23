from fastapi import FastAPI, Depends
from auth.router import router as auth_router
from auth.models import User
from auth.router import get_current_user
from auth.schemas import UserOut

app = FastAPI(
    title="Invitation App API",
    description="Backend для создания страниц-приглашений (свадьбы, дни рождения и т.д.)",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.include_router(auth_router)



@app.get("/")
async def root():
    return {"message": "Invitation backend is running"}


@app.get("/users/me", response_model=UserOut)
async def read_users_me(current_user: User = Depends(get_current_user)):
    return current_user