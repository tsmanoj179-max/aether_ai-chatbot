import json
import os
import base64
import asyncio
import logging
from typing import AsyncGenerator, Optional, List, Dict, Any
from sqlalchemy.orm import Session

from backend.app.config import settings
from backend.app.models.conversation import Conversation
from backend.app.models.message import Message
from backend.app.models.document import Document
from backend.app.providers.registry import provider_registry
from backend.app.services.document_service import document_service
from backend.app.services.memory_service import memory_service
from backend.app.services.search_service import search_service
from backend.app.services.research_service import research_service
from backend.app.services.tool_registry import tool_registry
from backend.app.services.image_service import image_service

logger = logging.getLogger("aetherai.chat")

class ChatService:
    def get_or_create_conversation(
        self,
        db: Session,
        conversation_id: Optional[str] = None,
        model_id: str = "aether-mock-omni",
        title: Optional[str] = None
    ) -> Conversation:
        if conversation_id:
            conv = db.query(Conversation).filter(Conversation.id == conversation_id).first()
            if conv:
                return conv

        new_conv = Conversation(
            title=title or "New Conversation",
            model_id=model_id
        )
        db.add(new_conv)
        db.commit()
        db.refresh(new_conv)
        return new_conv

    async def stream_chat_response(
        self,
        db: Session,
        conversation_id: str,
        user_message: str,
        model_id: Optional[str] = None,
        system_prompt: Optional[str] = None,
        web_search: bool = False,
        deep_research: bool = False,
        collection_name: Optional[str] = None,
        attachments: Optional[List[Dict[str, Any]]] = None,
        temperature: float = 0.7,
    ) -> AsyncGenerator[str, None]:
        """
        Main multi-provider conversational orchestrator.
        Formats SSE stream lines: data: {"type": ..., "data": ...}\n\n
        """
        conv = self.get_or_create_conversation(db, conversation_id, model_id or "aether-mock-omni")
        target_model = model_id or conv.model_id or "aether-mock-omni"

        # 1. Persist User Message
        user_msg = Message(
            conversation_id=conv.id,
            role="user",
            content=user_message,
            attachments=attachments
        )
        db.add(user_msg)
        db.commit()

        # Update conversation title if first user message
        if conv.title == "New Conversation":
            clean_title = user_message.strip()[:40] + ("..." if len(user_message.strip()) > 40 else "")
            conv.title = clean_title or "New Conversation"
            db.commit()

        # Emit Conversation metadata to client
        yield f"data: {json.dumps({'type': 'init', 'data': {'conversation_id': conv.id, 'title': conv.title}})}\n\n"

        # Handle Deep Research workflow if requested
        if deep_research:
            full_content = ""
            citations = []
            async for ev in research_service.run_deep_research_stream(user_message):
                yield f"data: {json.dumps(ev)}\n\n"
                if ev.get("type") == "token":
                    full_content += ev.get("data", {}).get("token", "")
                elif ev.get("type") == "citation":
                    citations.append(ev.get("data", {}))

            # Persist assistant response
            asst_msg = Message(
                conversation_id=conv.id,
                role="assistant",
                content=full_content,
                model_used=target_model,
                provider_used="deep_research",
                finish_reason="stop",
                citations=citations
            )
            db.add(asst_msg)
            db.commit()
            return

        # Check Image Generation Intent (e.g. "draw a sunset", "generate an image of a cat")
        img_intent = image_service.detect_image_generation_intent(user_message)
        if img_intent:
            yield f"data: {json.dumps({'type': 'status', 'data': {'status': '🎨 Synthesizing high-resolution image using FLUX.1 neural engine...', 'provider': 'image_generator'}})}\n\n"
            try:
                img_res = await image_service.generate_image(
                    prompt=img_intent["prompt"],
                    aspect_ratio=img_intent.get("aspect_ratio", "1:1"),
                    style=img_intent.get("style", "photorealistic")
                )
                yield f"data: {json.dumps({'type': 'image', 'data': img_res})}\n\n"

                img_url = img_res.get("url")
                raw_prompt = img_res.get("prompt")
                style_name = img_res.get("style", "photorealistic").replace("_", " ").title()
                aspect = img_res.get("aspect_ratio", "1:1")

                full_content = (
                    f"I have created your artwork using the **FLUX.1 Neural Engine**:\n\n"
                    f"![{raw_prompt}]({img_url})\n\n"
                    f"- **Prompt**: *\"{raw_prompt}\"*\n"
                    f"- **Artistic Style**: `{style_name}`\n"
                    f"- **Aspect Ratio**: `{aspect}`\n\n"
                    f"*You can request modifications (e.g. 'add neon lighting', 'switch to anime style', or 'make it landscape 16:9').*"
                )

                # Stream tokens smoothly to client
                words = full_content.split(" ")
                for i in range(0, len(words), 3):
                    chunk_text = " ".join(words[i:i+3]) + " "
                    yield f"data: {json.dumps({'type': 'token', 'data': {'token': chunk_text}})}\n\n"
                    await asyncio.sleep(0.01)

                yield f"data: {json.dumps({'type': 'done', 'data': {'model_used': 'flux.1', 'provider_used': 'image_generator', 'finish_reason': 'stop'}})}\n\n"

                asst_msg = Message(
                    conversation_id=conv.id,
                    role="assistant",
                    content=full_content,
                    model_used="flux.1",
                    provider_used="image_generator",
                    finish_reason="stop",
                    attachments=[img_res]
                )
                db.add(asst_msg)
                db.commit()
                return
            except Exception as e:
                logger.error(f"Image generation failed: {e}")
                yield f"data: {json.dumps({'type': 'status', 'data': {'status': f'Image generation error: {e}. Transitioning to text reasoning...'}})}\n\n"

        # 2. Context assembly
        assembled_system_parts = []
        if system_prompt:
            assembled_system_parts.append(system_prompt)
        elif conv.system_prompt:
            assembled_system_parts.append(conv.system_prompt)
        else:
            assembled_system_parts.append(
                "You are AetherAI, a sophisticated, helpful, and highly capable AI workspace assistant."
            )

        # Inject long-term memory
        mem_text, mem_ids = memory_service.get_relevant_memories_prompt(db, user_message)
        if mem_text:
            assembled_system_parts.append(f"\n{mem_text}")

        # Inject RAG document context if collection specified
        rag_citations = []
        if collection_name:
            yield f"data: {json.dumps({'type': 'status', 'data': {'status': f'Retrieving relevant passages from Knowledge Collection: {collection_name}...'}})}\n\n"
            rag_results = document_service.search_collection(db, user_message, collection_name=collection_name, top_k=4)
            if rag_results:
                doc_context_str = "\n\nRetrieved Knowledge Passages from User Documents:\n"
                for res in rag_results:
                    doc_context_str += f"- [{res.filename} (Page {res.page_number or 1})]: {res.content}\n"
                    rag_citations.append({
                        "title": f"{res.filename} (p. {res.page_number or 1})",
                        "url": f"doc://{res.document_id}#chunk={res.chunk_id}",
                        "snippet": res.content[:200]
                    })
                assembled_system_parts.append(doc_context_str)
                for cite in rag_citations:
                    yield f"data: {json.dumps({'type': 'citation', 'data': cite})}\n\n"

        # Web search if enabled
        search_citations = []
        if web_search:
            yield f"data: {json.dumps({'type': 'status', 'data': {'status': 'Searching live web sources...'}})}\n\n"
            web_results = await search_service.search(user_message, max_results=3)
            if web_results:
                search_str = "\n\nLive Web Search Results:\n"
                for wr in web_results:
                    search_str += f"- [{wr['title']}] ({wr['url']}): {wr['snippet']}\n"
                    search_citations.append(wr)
                    yield f"data: {json.dumps({'type': 'citation', 'data': wr})}\n\n"
                assembled_system_parts.append(search_str)

        # Multimodal Vision Analysis for Image Attachments
        attached_image_blocks: List[str] = []
        raw_image_parts: List[Dict[str, Any]] = []

        if attachments:
            for att in attachments:
                fname = att.get("filename", "image.jpg")
                fpath = att.get("file_path", "")
                doc_id = att.get("doc_id") or att.get("id")
                ftype = att.get("file_type", "") or os.path.splitext(fname)[1].lower()
                is_image = (
                    ftype in [".png", ".jpg", ".jpeg", ".webp", ".bmp", ".gif"]
                    or "image" in str(att.get("file_type", "")).lower()
                    or any(fname.lower().endswith(x) for x in [".png", ".jpg", ".jpeg", ".webp", ".bmp", ".gif"])
                )

                if is_image:
                    yield f"data: {json.dumps({'type': 'status', 'data': {'status': f'🔍 Inspecting visual elements of {fname}...'}})}\n\n"
                    img_bytes = None

                    # Source 1: Direct base64 string
                    if att.get("base64"):
                        try:
                            raw_b64 = att["base64"]
                            if "," in raw_b64:
                                raw_b64 = raw_b64.split(",", 1)[1]
                            img_bytes = base64.b64decode(raw_b64)
                        except Exception as e:
                            logger.warning(f"Error decoding base64: {e}")

                    # Source 2: Lookup document in database via doc_id
                    if not img_bytes and doc_id:
                        doc_rec = db.query(Document).filter(Document.id == doc_id).first()
                        if doc_rec and doc_rec.file_path and os.path.exists(doc_rec.file_path):
                            try:
                                with open(doc_rec.file_path, "rb") as f:
                                    img_bytes = f.read()
                            except Exception as e:
                                logger.warning(f"Error reading doc_rec.file_path: {e}")

                    # Source 3: Direct local file_path
                    if not img_bytes and fpath and os.path.exists(fpath):
                        try:
                            with open(fpath, "rb") as f:
                                img_bytes = f.read()
                        except Exception as e:
                            logger.warning(f"Error reading fpath: {e}")

                    # Source 4: Search UPLOAD_DIR for matching filename or doc_id
                    if not img_bytes:
                        upload_dir = settings.UPLOAD_DIR
                        if os.path.exists(upload_dir):
                            for root, _, files in os.walk(upload_dir):
                                for fl in files:
                                    if fl == fname or fl.endswith(f"_{fname}") or (doc_id and doc_id in fl):
                                        candidate = os.path.join(root, fl)
                                        if os.path.exists(candidate):
                                            try:
                                                with open(candidate, "rb") as f:
                                                    img_bytes = f.read()
                                                break
                                            except Exception:
                                                pass
                                if img_bytes:
                                    break

                    if img_bytes:
                        mime_sub = ftype.replace(".", "") if ftype.startswith(".") else "jpeg"
                        if "png" in mime_sub:
                            resolved_mime = "image/png"
                        elif "webp" in mime_sub:
                            resolved_mime = "image/webp"
                        else:
                            resolved_mime = "image/jpeg"

                        analysis_res = await image_service.analyze_image_multimodal(
                            image_bytes=img_bytes,
                            mime_type=resolved_mime,
                            question=user_message,
                            model_id=target_model,
                            filename=fname
                        )
                        block = f"--- Attached Image: {fname} ---\n{analysis_res['analysis']}\n--- End of Attached Image ---"
                        attached_image_blocks.append(block)
                        assembled_system_parts.append(
                            f"\n\n[Attached Image Visual Breakdown for '{fname}']:\n{analysis_res['analysis']}\n"
                        )
                        raw_image_parts.append({
                            "bytes": img_bytes,
                            "mime_type": resolved_mime,
                            "filename": fname
                        })

        if attached_image_blocks:
            assembled_system_parts.append(
                "\n\n[CRITICAL MULTIMODAL INSTRUCTION]:\n"
                "The user has attached image(s) to this message. You have been provided with detailed "
                "visual telemetry, optical character recognition (OCR) text, and composition data above. "
                "You MUST answer questions about the image(s) directly, accurately, and authoritatively. "
                "NEVER say 'I cannot view attachments' or 'I am unable to see the image', because "
                "you HAVE already been provided with the complete visual contents and breakdown."
            )

        final_system_prompt = "\n".join(assembled_system_parts)

        # 3. Retrieve recent conversation history (Context Window Management)
        recent_messages = (
            db.query(Message)
            .filter(Message.conversation_id == conv.id)
            .order_by(Message.created_at.desc())
            .limit(10)
            .all()
        )
        recent_messages.reverse()

        messages_payload = [
            {"role": m.role, "content": m.content}
            for m in recent_messages
        ]

        # Augment the last user turn with visual details and raw image bytes
        if attached_image_blocks and messages_payload:
            visual_context_str = "\n\n".join(attached_image_blocks)
            augmented_content = (
                f"[Attached Image Inspection & Visual Data]:\n"
                f"{visual_context_str}\n\n"
                f"[User Request]:\n"
                f"{user_message}"
            )
            # Find the last user turn and augment it
            for idx in range(len(messages_payload) - 1, -1, -1):
                if messages_payload[idx]["role"] == "user":
                    messages_payload[idx]["content"] = augmented_content
                    if raw_image_parts:
                        messages_payload[idx]["images"] = raw_image_parts
                    break

        # 4. Stream response via Provider Registry with Failover
        full_content = ""
        model_used = target_model
        provider_used = "mock"
        finish_reason = "stop"
        collected_tool_calls = []

        try:
            async for chunk in provider_registry.execute_stream_with_failover(
                messages=messages_payload,
                model_id=target_model,
                temperature=temperature,
                system_prompt=final_system_prompt
            ):
                chunk_type = chunk.get("type")
                if chunk_type == "token":
                    token = chunk.get("data", {}).get("token", "")
                    full_content += token
                    yield f"data: {json.dumps(chunk)}\n\n"
                elif chunk_type == "citation":
                    cite = chunk.get("data", {})
                    search_citations.append(cite)
                    yield f"data: {json.dumps(chunk)}\n\n"
                elif chunk_type == "done":
                    done_data = chunk.get("data", {})
                    model_used = done_data.get("model_used", target_model)
                    provider_used = done_data.get("provider_used", "mock")
                    finish_reason = done_data.get("finish_reason", "stop")
                    yield f"data: {json.dumps(chunk)}\n\n"
                else:
                    yield f"data: {json.dumps(chunk)}\n\n"

        except Exception as e:
            logger.error(f"Streaming error: {e}")
            yield f"data: {json.dumps({'type': 'error', 'data': {'error': str(e)}})}\n\n"

        # 5. Persist final Assistant message to database
        all_citations = rag_citations + search_citations
        asst_msg = Message(
            conversation_id=conv.id,
            role="assistant",
            content=full_content,
            model_used=model_used,
            provider_used=provider_used,
            finish_reason=finish_reason,
            citations=all_citations if all_citations else None,
            tool_calls=collected_tool_calls if collected_tool_calls else None
        )
        db.add(asst_msg)
        db.commit()

chat_service = ChatService()
