import os
import glob
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Body
from pydantic import BaseModel, Field

from backend.app.config import settings
from backend.app.services.image_service import image_service, STYLE_MODIFIERS, ASPECT_RATIOS

router = APIRouter(prefix="/images", tags=["Image Generation & Vision"])

class ImageGenerateRequest(BaseModel):
    prompt: str = Field(..., min_length=2, max_length=1000, description="Visual description of the desired image")
    style: Optional[str] = Field("photorealistic", description="Artistic style preset")
    aspect_ratio: Optional[str] = Field("1:1", description="1:1, 16:9, 9:16, 4:3")
    seed: Optional[int] = Field(None, description="Optional seed for deterministic generation")

class ImageGenerateResponse(BaseModel):
    id: str
    url: str
    remote_url: Optional[str] = None
    prompt: str
    enhanced_prompt: str
    style: str
    aspect_ratio: str
    width: int
    height: int
    provider: str
    created_at: str

class ImageStyleInfo(BaseModel):
    id: str
    name: str
    description: str

@router.get("/styles")
def get_available_styles():
    """Returns available artistic style presets and aspect ratios for image generation."""
    styles = []
    for k, v in STYLE_MODIFIERS.items():
        name = k.replace("_", " ").title()
        styles.append({"id": k, "name": name, "description": v[:60] + "..."})
    return {
        "styles": styles,
        "aspect_ratios": list(ASPECT_RATIOS.keys())
    }

@router.post("/generate", response_model=ImageGenerateResponse)
async def generate_image(request: ImageGenerateRequest):
    """
    Generates a high-resolution image from text description using FLUX.1 / DALL-E.
    Zero-key required for instant free cloud generation.
    """
    try:
        result = await image_service.generate_image(
            prompt=request.prompt,
            aspect_ratio=request.aspect_ratio or "1:1",
            style=request.style or "photorealistic",
            seed=request.seed
        )
        return ImageGenerateResponse.model_validate(result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Image generation failed: {str(e)}")

@router.post("/analyze")
async def analyze_image_upload(
    file: UploadFile = File(...),
    question: Optional[str] = Form(None)
):
    """
    Analyzes an uploaded image, extracting visual properties, dominant colors,
    geometry, and semantic multimodal explanations.
    """
    ext = os.path.splitext(file.filename or "")[1].lower()
    if ext not in [".png", ".jpg", ".jpeg", ".webp"]:
        raise HTTPException(status_code=400, detail="Only PNG, JPG, JPEG, and WEBP image files are supported.")

    content = await file.read()
    if len(content) > 20 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="Image exceeds maximum 20MB limit.")

    mime_type = file.content_type or f"image/{ext.replace('.', '')}"
    result = await image_service.analyze_image_multimodal(
        image_bytes=content,
        mime_type=mime_type,
        question=question
    )
    return result

@router.get("/gallery")
def get_image_gallery(limit: int = 30):
    """Lists recently generated images stored on disk for visual studio browsing."""
    generated_dir = os.path.join(settings.UPLOAD_DIR, "generated")
    if not os.path.exists(generated_dir):
        return {"count": 0, "images": []}

    files = glob.glob(os.path.join(generated_dir, "*.jpg"))
    files.sort(key=os.path.getmtime, reverse=True)

    items = []
    for f in files[:limit]:
        fname = os.path.basename(f)
        items.append({
            "id": fname.replace(".jpg", ""),
            "filename": fname,
            "url": f"/uploads/generated/{fname}",
            "created_at": datetime.fromtimestamp(os.path.getmtime(f), tz=timezone.utc).isoformat(),
            "size": os.path.getsize(f),
            "prompt": "Generated Artwork",
            "style": "photorealistic",
            "aspect_ratio": "1:1",
            "width": 1024,
            "height": 1024,
            "provider": "FLUX.1"
        })
    return {"count": len(items), "images": items}
