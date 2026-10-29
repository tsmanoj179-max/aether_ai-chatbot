from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from backend.app.database import get_db
from backend.app.models.setting import Setting
from backend.app.schemas.settings import UserSettings

router = APIRouter(prefix="/settings", tags=["User Settings"])

DEFAULT_SETTINGS_KEY = "user_preferences"

@router.get("", response_model=UserSettings)
def get_user_settings(db: Session = Depends(get_db)):
    setting_row = db.query(Setting).filter(Setting.key == DEFAULT_SETTINGS_KEY).first()
    if setting_row and isinstance(setting_row.value, dict):
        return UserSettings(**setting_row.value)
    return UserSettings()

@router.post("", response_model=UserSettings)
def update_user_settings(
    payload: UserSettings,
    db: Session = Depends(get_db)
):
    setting_row = db.query(Setting).filter(Setting.key == DEFAULT_SETTINGS_KEY).first()
    if not setting_row:
        setting_row = Setting(key=DEFAULT_SETTINGS_KEY, value=payload.dict())
        db.add(setting_row)
    else:
        setting_row.value = payload.dict()

    db.commit()
    db.refresh(setting_row)
    return UserSettings(**setting_row.value)
