from fastapi import APIRouter

router = APIRouter()


@router.get("/")
async def health():
    return {"msg": "Welcome to the Trading Bot Platform Backend!"}
