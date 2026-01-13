from fastapi import APIRouter
from database import toggle_db_mode, get_db_mode

router = APIRouter()


@router.post("/migrate")
def switch_mode():
    return {"mode": toggle_db_mode()}


@router.get("/mode")
def get_mode():
    return {"mode": get_db_mode()}
