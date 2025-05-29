from fastapi import APIRouter

router = APIRouter()


@router.post("/")
async def auth():
    return {"msg": "Welcome to the Auth route"}
