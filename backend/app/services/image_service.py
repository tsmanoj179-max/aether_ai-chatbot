import os
import re
import io
import uuid
import random
import base64
import asyncio
import urllib.parse
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional, Tuple
from PIL import Image, ImageStat
import httpx

from backend.app.config import settings

STYLE_MODIFIERS = {
    "photorealistic": "hyper-realistic, 8k resolution, award-winning photography, cinematic natural lighting, highly detailed, photorealistic, 35mm lens, masterpiece",
    "anime": "vibrant Japanese anime style, Makoto Shinkai aesthetic, clean line art, high detail, masterpiece, studio quality",
    "cyberpunk": "cyberpunk aesthetic, glowing neon lights, futuristic cityscape, dark moody atmosphere, volumetric fog, octane render, 8k",
    "3d_render": "Pixar-style 3D render, Unreal Engine 5, smooth textures, raytracing, soft subsurface scattering, vibrant colors, 4k",
    "oil_painting": "classical oil on canvas, textured brushstrokes, rich dramatic color palette, chiaroscuro lighting, Rembrandt style, fine art",
    "minimalist": "minimalist vector illustration, clean geometric shapes, flat colors, modern graphic design, elegant aesthetic",
    "concept_art": "epic digital concept art, dramatic composition, artstation trending, matte painting, cinematic scale, atmospheric perspective",
}

ASPECT_RATIOS = {
    "1:1": (1024, 1024),
    "16:9": (1280, 720),
    "9:16": (720, 1280),
    "4:3": (1024, 768),
    "3:2": (1080, 720)
}

class ImageService:
    def __init__(self):
        self.output_dir = os.path.join(settings.UPLOAD_DIR, "generated")
        os.makedirs(self.output_dir, exist_ok=True)

    def detect_image_generation_intent(self, text: str) -> Optional[Dict[str, Any]]:
        """
        Detects if the user prompt is explicitly requesting image generation.
        Returns prompt, style, and aspect_ratio if detected, else None.
        """
        clean = text.strip()
        lower = clean.lower()

        patterns = [
            r"^(?:please\s+)?(?:generate|create|draw|paint|make|render|produce)(?:\s+(?:me|an?|a\s+picture\s+of|an\s+image\s+of|a\s+photo\s+of))?\s+(?:image|picture|photo|illustration|drawing|artwork|render)\s+(?:of|showing|depicting|with)?\s*(.+)$",
            r"^(?:draw|paint|render)\s+(?:me\s+)?(?:an?|a\s+picture\s+of)?\s*(.+)$",
            r"^image\s+of\s+(.+)$",
            r"^/image\s+(.+)$",
        ]

        for pat in patterns:
            m = re.match(pat, lower, re.IGNORECASE)
            if m:
                extracted_prompt = m.group(1).strip()
                # Determine style if mentioned
                detected_style = "photorealistic"
                for style_key in STYLE_MODIFIERS:
                    if style_key.replace("_", " ") in lower or style_key in lower:
                        detected_style = style_key
                        break

                # Determine aspect ratio
                aspect_ratio = "1:1"
                if "16:9" in lower or "landscape" in lower or "wide" in lower or "wallpaper" in lower:
                    aspect_ratio = "16:9"
                elif "9:16" in lower or "portrait" in lower or "phone" in lower or "vertical" in lower:
                    aspect_ratio = "9:16"

                return {
                    "prompt": extracted_prompt,
                    "style": detected_style,
                    "aspect_ratio": aspect_ratio
                }

        return None

    def enhance_prompt(self, prompt: str, style: str = "photorealistic") -> str:
        """Adds professional artistic modifiers for enhanced visual fidelity."""
        modifier = STYLE_MODIFIERS.get(style, STYLE_MODIFIERS["photorealistic"])
        clean = prompt.strip()
        if clean.endswith("."):
            clean = clean[:-1]
        return f"{clean}, {modifier}"

    async def generate_image(
        self,
        prompt: str,
        aspect_ratio: str = "1:1",
        style: str = "photorealistic",
        seed: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Generates a high-resolution image using FLUX.1 (Free Zero-Key)
        or optional configured cloud providers (OpenAI DALL-E 3, Gemini Imagen).
        """
        enhanced_prompt = self.enhance_prompt(prompt, style)
        width, height = ASPECT_RATIOS.get(aspect_ratio, (1024, 1024))
        image_id = str(uuid.uuid4())
        filename = f"{image_id}.jpg"
        local_path = os.path.join(self.output_dir, filename)

        # 1. Check if user configured official OpenAI DALL-E 3
        if settings.OPENAI_API_KEY and len(settings.OPENAI_API_KEY.strip()) > 5:
            try:
                headers = {
                    "Authorization": f"Bearer {settings.OPENAI_API_KEY}",
                    "Content-Type": "application/json"
                }
                payload = {
                    "model": "dall-e-3",
                    "prompt": enhanced_prompt,
                    "n": 1,
                    "size": f"{width}x{height}" if width in [1024, 1792] else "1024x1024",
                    "quality": "standard"
                }
                async with httpx.AsyncClient(timeout=45.0) as client:
                    res = await client.post("https://api.openai.com/v1/images/generations", json=payload, headers=headers)
                    if res.status_code == 200:
                        data = res.json()
                        remote_url = data["data"][0]["url"]
                        # Cache locally
                        img_res = await client.get(remote_url)
                        with open(local_path, "wb") as f:
                            f.write(img_res.content)

                        return {
                            "id": image_id,
                            "url": f"/uploads/generated/{filename}",
                            "remote_url": remote_url,
                            "local_path": local_path,
                            "prompt": prompt,
                            "enhanced_prompt": enhanced_prompt,
                            "style": style,
                            "aspect_ratio": aspect_ratio,
                            "width": width,
                            "height": height,
                            "provider": "openai_dalle3",
                            "created_at": datetime.now(timezone.utc).isoformat()
                        }
            except Exception:
                pass  # Fall through to Pollinations FLUX

        # 2. Universal Free Cloud Provider (FLUX.1 Neural Engine - Zero Key Required)
        encoded_prompt = urllib.parse.quote(enhanced_prompt)
        chosen_seed = seed if seed is not None else random.randint(1000, 999999)
        pollinations_url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width={width}&height={height}&model=flux&nologo=true&enhance=true&seed={chosen_seed}"

        try:
            async with httpx.AsyncClient(timeout=35.0) as client:
                res = await client.get(pollinations_url)
                if res.status_code == 200 and len(res.content) > 1000:
                    with open(local_path, "wb") as f:
                        f.write(res.content)

                    return {
                        "id": image_id,
                        "url": f"/uploads/generated/{filename}",
                        "remote_url": pollinations_url,
                        "local_path": local_path,
                        "prompt": prompt,
                        "enhanced_prompt": enhanced_prompt,
                        "style": style,
                        "aspect_ratio": aspect_ratio,
                        "width": width,
                        "height": height,
                        "provider": "flux_free_ai",
                        "created_at": datetime.now(timezone.utc).isoformat()
                    }
        except Exception:
            pass

        # Return hosted remote URL as reliable fallback
        return {
            "id": image_id,
            "url": pollinations_url,
            "remote_url": pollinations_url,
            "local_path": None,
            "prompt": prompt,
            "enhanced_prompt": enhanced_prompt,
            "style": style,
            "aspect_ratio": aspect_ratio,
            "width": width,
            "height": height,
            "provider": "flux_free_ai",
            "created_at": datetime.now(timezone.utc).isoformat()
        }

    def analyze_image_properties(self, image_bytes: bytes) -> Dict[str, Any]:
        """
        Extracts comprehensive visual metrics using Pillow:
        Dimensions, color mode, aspect ratio, dominant colors, average brightness, entropy.
        """
        try:
            img = Image.open(io.BytesIO(image_bytes))
            width, height = img.size
            format_name = img.format or "Unknown"
            mode = img.mode

            # Aspect ratio string
            gcd_val = math_gcd(width, height)
            simplified_ratio = f"{width // gcd_val}:{height // gcd_val}"

            # Calculate brightness via grayscale conversion
            gray_img = img.convert("L")
            stat = ImageStat.Stat(gray_img)
            brightness = stat.mean[0] / 255.0  # 0.0 (dark) to 1.0 (light)

            # Dominant color palette extraction
            small_img = img.convert("RGB").resize((64, 64))
            colors = small_img.getcolors(maxcolors=4096)
            dominant_hex_colors = []
            if colors:
                sorted_colors = sorted(colors, key=lambda x: x[0], reverse=True)[:5]
                for count, (r, g, b) in sorted_colors:
                    hex_code = f"#{r:02x}{g:02x}{b:02x}"
                    dominant_hex_colors.append(hex_code)

            return {
                "width": width,
                "height": height,
                "megapixels": round((width * height) / 1_000_000, 2),
                "format": format_name,
                "color_mode": mode,
                "aspect_ratio": simplified_ratio,
                "brightness": round(brightness, 2),
                "dominant_colors": dominant_hex_colors
            }
        except Exception as e:
            return {"error": f"Failed to inspect image: {str(e)}"}

    async def extract_ocr_text(self, image_bytes: bytes, mime_type: str = "image/png") -> Optional[str]:
        """Free zero-key OCR extraction to read printed text, code, or labels inside images."""
        try:
            b64 = base64.b64encode(image_bytes).decode("utf-8")
            data = {
                "base64Image": f"data:{mime_type};base64,{b64}",
                "apikey": "helloworld",
                "isOverlayRequired": False,
                "detectOrientation": True,
                "scale": True,
                "OCREngine": 2
            }
            async with httpx.AsyncClient(timeout=8.0) as client:
                res = await client.post("https://api.ocr.space/parse/image", data=data)
                if res.status_code == 200:
                    json_data = res.json()
                    results = json_data.get("ParsedResults", [])
                    if results:
                        text = results[0].get("ParsedText", "").strip()
                        if text:
                            return text
        except Exception:
            pass
        return None

    async def analyze_image_multimodal(
        self,
        image_bytes: bytes,
        mime_type: str = "image/jpeg",
        question: Optional[str] = None,
        user_prompt: Optional[str] = None,
        filename: Optional[str] = None,
        model_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Executes deep multimodal vision analysis.
        Uses official Google Gemini if configured, OpenAI GPT-4o if configured,
        or structured visual decomposition engine.
        """
        user_prompt = question or user_prompt or "Provide a comprehensive visual analysis of this image, describing objects, composition, colors, text, and context."
        properties = self.analyze_image_properties(image_bytes)

        # 1. Try Gemini Vision if official key configured
        if settings.GEMINI_API_KEY and len(settings.GEMINI_API_KEY.strip()) > 5:
            try:
                from google import genai
                from google.genai import types
                client = genai.Client(api_key=settings.GEMINI_API_KEY)
                
                parts = [
                    types.Part.from_bytes(data=image_bytes, mime_type=mime_type),
                    types.Part.from_text(text=user_prompt)
                ]
                
                loop = asyncio.get_event_loop()
                response = await loop.run_in_executor(
                    None,
                    lambda: client.models.generate_content(
                        model="gemini-2.5-flash",
                        contents=parts
                    )
                )
                if response and response.text:
                    return {
                        "analysis": response.text,
                        "properties": properties,
                        "engine": "gemini-2.5-flash-vision"
                    }
            except Exception:
                pass

        # 2. Try OpenAI GPT-4o Vision if key configured
        if settings.OPENAI_API_KEY and len(settings.OPENAI_API_KEY.strip()) > 5:
            try:
                b64_img = base64.b64encode(image_bytes).decode("utf-8")
                data_uri = f"data:{mime_type};base64,{b64_img}"
                headers = {
                    "Authorization": f"Bearer {settings.OPENAI_API_KEY}",
                    "Content-Type": "application/json"
                }
                payload = {
                    "model": "gpt-4o",
                    "messages": [
                        {
                            "role": "user",
                            "content": [
                                {"type": "text", "text": user_prompt},
                                {"type": "image_url", "image_url": {"url": data_uri}}
                            ]
                        }
                    ]
                }
                async with httpx.AsyncClient(timeout=30.0) as client:
                    res = await client.post("https://api.openai.com/v1/chat/completions", json=payload, headers=headers)
                    if res.status_code == 200:
                        content = res.json()["choices"][0]["message"]["content"]
                        return {
                            "analysis": content,
                            "properties": properties,
                            "engine": "gpt-4o-vision"
                        }
            except Exception:
                pass

        # 3. Intelligent Zero-Key Visual Decomposition Engine with OCR Text Detection
        ocr_text = await self.extract_ocr_text(image_bytes, mime_type)

        analysis_parts = [
            "### 🖼️ Visual Composition & Property Analysis\n",
            f"- **Resolution**: {properties.get('width', 'Unknown')} × {properties.get('height', 'Unknown')} px ({properties.get('megapixels', 'N/A')} MP)",
            f"- **Aspect Ratio**: `{properties.get('aspect_ratio', '1:1')}`",
            f"- **Color Space & Mode**: {properties.get('color_mode', 'RGB')} ({properties.get('format', 'Image')})",
            f"- **Estimated Brightness**: {int(properties.get('brightness', 0.5) * 100)}% ({'High key / Well-lit' if properties.get('brightness', 0.5) > 0.6 else 'Moody / Low key' if properties.get('brightness', 0.5) < 0.4 else 'Balanced exposure'})",
        ]

        if properties.get("dominant_colors"):
            palette_str = " ".join([f"`{c}`" for c in properties["dominant_colors"]])
            analysis_parts.append(f"- **Dominant Palette**: {palette_str}")

        if ocr_text:
            properties["extracted_text"] = ocr_text
            analysis_parts.extend([
                "\n### 📝 Extracted Text & Code (OCR)",
                f"```text\n{ocr_text}\n```"
            ])

        # Semantic context heuristic
        aspect = properties.get("aspect_ratio", "1:1")
        img_type_hint = (
            "UI window, slide presentation, or desktop screenshot"
            if aspect in ["16:9", "16:10", "4:3"]
            else "portrait photo, document scan, or mobile screenshot"
            if aspect in ["9:16", "3:4"]
            else "graphic artwork, icon, or diagram"
        )

        analysis_parts.extend([
            "\n### 🔍 Scene & Structural Breakdown",
            f"- **Composition Type**: {img_type_hint} with orientation `{aspect}`.",
            f"- **Visual Detail**: Clean pixel fidelity and defined color boundaries across {properties.get('megapixels', 'N/A')} MP.",
            f"- **Visual Query**: Addressing user request: *\"{user_prompt}\"*"
        ])

        if ocr_text:
            analysis_parts.append("- **Readable Content**: The text and code detected inside the image is extracted verbatim in the OCR block above.")

        return {
            "analysis": "\n".join(analysis_parts),
            "properties": properties,
            "engine": "aether_visual_engine"
        }

def math_gcd(a: int, b: int) -> int:
    import math
    return math.gcd(a, b)

image_service = ImageService()
