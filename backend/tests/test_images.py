import io
import pytest
from PIL import Image
from backend.app.services.image_service import image_service
from backend.app.services.tool_registry import tool_registry


def _create_sample_image_bytes(width: int = 120, height: int = 80, color: str = "red") -> bytes:
    img = Image.new("RGB", (width, height), color=color)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def test_image_intent_detection():
    # Prompt variations
    res1 = image_service.detect_image_generation_intent("draw a neon cybernetic owl")
    assert res1 is not None
    assert "neon cybernetic owl" in res1["prompt"]

    res2 = image_service.detect_image_generation_intent("please generate an image of a tranquil mountain lake with sunset --style anime")
    assert res2 is not None

    res3 = image_service.detect_image_generation_intent("how do I configure a FastAPI server?")
    assert res3 is None


def test_image_property_analysis():
    img_bytes = _create_sample_image_bytes(200, 100, color="blue")
    props = image_service.analyze_image_properties(img_bytes)

    assert props["width"] == 200
    assert props["height"] == 100
    assert props["format"] == "PNG"
    assert props["aspect_ratio"] == "2:1"
    assert "dominant_colors" in props
    assert len(props["dominant_colors"]) > 0


@pytest.mark.asyncio
async def test_image_multimodal_analysis():
    img_bytes = _create_sample_image_bytes(100, 100, color="green")
    res = await image_service.analyze_image_multimodal(
        image_bytes=img_bytes,
        mime_type="image/png",
        user_prompt="Analyze the composition of this green test square."
    )

    assert "analysis" in res
    assert "properties" in res
    assert res["properties"]["width"] == 100
    assert res["properties"]["height"] == 100
    assert "engine" in res


def test_images_api_styles_and_gallery(client):
    # 1. Styles endpoint
    res = client.get("/api/v1/images/styles")
    assert res.status_code == 200
    data = res.json()
    assert "styles" in data
    style_ids = [s["id"] for s in data["styles"]]
    assert "photorealistic" in style_ids
    assert "aspect_ratios" in data

    # 2. Gallery endpoint
    res_gal = client.get("/api/v1/images/gallery")
    assert res_gal.status_code == 200
    gal_data = res_gal.json()
    assert "images" in gal_data
    assert "count" in gal_data


def test_images_api_analyze_upload(client):
    img_bytes = _create_sample_image_bytes(150, 100, color="purple")
    files = {"file": ("test_sample.png", img_bytes, "image/png")}
    data = {"question": "Describe what you see in this purple rectangle."}

    res = client.post("/api/v1/images/analyze", files=files, data=data)
    assert res.status_code == 200
    res_json = res.json()
    assert "analysis" in res_json
    assert "properties" in res_json
    assert res_json["properties"]["width"] == 150
    assert res_json["properties"]["height"] == 100


@pytest.mark.asyncio
async def test_tool_registry_image_tool():
    # Verify generate_image is registered
    tools = tool_registry.list_tools()
    tool_names = [t["name"] for t in tools]
    assert "generate_image" in tool_names


def test_chat_stream_with_image_attachment(client):
    import base64
    img_bytes = _create_sample_image_bytes(80, 80, color="orange")
    b64_str = base64.b64encode(img_bytes).decode("utf-8")

    res = client.post(
        "/api/v1/chat/stream",
        json={
            "message": "What are the dimensions and dominant colors in this attached image?",
            "model_id": "aether-mock-omni",
            "attachments": [
                {
                    "filename": "orange_square.png",
                    "file_type": "image/png",
                    "file_size": len(img_bytes),
                    "base64": f"data:image/png;base64,{b64_str}"
                }
            ]
        }
    )
    assert res.status_code == 200
    body = res.text
    assert "data: " in body
    assert "Inspecting visual elements of orange_square.png" in body
    assert "done" in body
