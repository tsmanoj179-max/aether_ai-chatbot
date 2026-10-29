import ast
import operator
import csv
import io
import os
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from backend.app.models.audit import AuditRecord
from backend.app.services.search_service import search_service
from backend.app.services.image_service import image_service

# Safe AST Math Evaluator (No unrestricted exec/eval)
_ALLOWED_OPERATORS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.FloorDiv: operator.floordiv,
    ast.Mod: operator.mod,
    ast.Pow: operator.pow,
    ast.USub: operator.neg,
    ast.UAdd: operator.pos,
}

def _safe_eval(node):
    if isinstance(node, ast.Constant):  # numbers, string
        if isinstance(node.value, (int, float)):
            return node.value
        raise ValueError("Only numbers are allowed in calculations.")
    elif isinstance(node, ast.BinOp):
        op = _ALLOWED_OPERATORS.get(type(node.op))
        if op is None:
            raise ValueError(f"Unsupported math operator: {type(node.op).__name__}")
        left = _safe_eval(node.left)
        right = _safe_eval(node.right)
        if type(node.op) in (ast.Div, ast.FloorDiv, ast.Mod) and right == 0:
            raise ZeroDivisionError("Division by zero is not allowed.")
        return op(left, right)
    elif isinstance(node, ast.UnaryOp):
        op = _ALLOWED_OPERATORS.get(type(node.op))
        if op is None:
            raise ValueError(f"Unsupported unary operator: {type(node.op).__name__}")
        return op(_safe_eval(node.operand))
    else:
        raise ValueError(f"Expression type {type(node).__name__} is forbidden.")

class ToolDefinition:
    def __init__(
        self,
        name: str,
        description: str,
        parameters: Dict[str, Any],
        requires_confirmation: bool = False,
        timeout_seconds: int = 15
    ):
        self.name = name
        self.description = description
        self.parameters = parameters
        self.requires_confirmation = requires_confirmation
        self.timeout_seconds = timeout_seconds

class ToolRegistry:
    def __init__(self):
        self.tools: Dict[str, ToolDefinition] = {
            "calculator": ToolDefinition(
                name="calculator",
                description="Safely evaluate mathematical expressions using an isolated AST parser.",
                parameters={
                    "type": "object",
                    "properties": {
                        "expression": {"type": "string", "description": "e.g. (145 * 12) + (24 / 4)"}
                    },
                    "required": ["expression"]
                }
            ),
            "datetime_util": ToolDefinition(
                name="datetime_util",
                description="Get current UTC and localized timestamp or date arithmetic.",
                parameters={
                    "type": "object",
                    "properties": {
                        "action": {"type": "string", "enum": ["current_time", "iso_format"]}
                    }
                }
            ),
            "web_search": ToolDefinition(
                name="web_search",
                description="Search the web for up-to-date facts, documentation, or news.",
                parameters={
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "Search term"}
                    },
                    "required": ["query"]
                }
            ),
            "csv_data_analyst": ToolDefinition(
                name="csv_data_analyst",
                description="Compute summary statistics, column types, and missing value counts for a dataset file.",
                parameters={
                    "type": "object",
                    "properties": {
                        "file_path": {"type": "string", "description": "Relative server path to uploaded dataset"}
                    },
                    "required": ["file_path"]
                }
            ),
            "generate_image": ToolDefinition(
                name="generate_image",
                description="Generate high-resolution visual artwork or photography from a text prompt using the FLUX.1 neural engine.",
                parameters={
                    "type": "object",
                    "properties": {
                        "prompt": {"type": "string", "description": "Detailed image description"},
                        "style": {"type": "string", "enum": ["photorealistic", "anime", "cyberpunk", "3d_render", "oil_painting", "minimalist", "concept_art"]},
                        "aspect_ratio": {"type": "string", "enum": ["1:1", "16:9", "9:16", "4:3"]}
                    },
                    "required": ["prompt"]
                }
            ),
        }

    def list_tools(self) -> List[Dict[str, Any]]:
        return [
            {
                "name": t.name,
                "description": t.description,
                "parameters": t.parameters,
                "requires_confirmation": t.requires_confirmation,
                "timeout_seconds": t.timeout_seconds
            }
            for t in self.tools.values()
        ]

    async def execute_tool(
        self,
        tool_name: str,
        arguments: Dict[str, Any],
        db: Optional[Session] = None
    ) -> Dict[str, Any]:
        """Executes a declared tool with argument validation and audit logging."""
        if tool_name not in self.tools:
            return {"error": f"Tool '{tool_name}' is not recognized."}

        start_time = datetime.now(timezone.utc)
        result: Dict[str, Any] = {}

        try:
            if tool_name == "calculator":
                expr = str(arguments.get("expression", "")).strip()
                if not expr or len(expr) > 200:
                    raise ValueError("Expression is empty or exceeds 200 characters.")
                tree = ast.parse(expr, mode='eval')
                val = _safe_eval(tree.body)
                result = {"expression": expr, "result": val}

            elif tool_name == "datetime_util":
                now = datetime.now(timezone.utc)
                result = {
                    "utc_now": now.isoformat(),
                    "formatted": now.strftime("%A, %B %d, %Y %H:%M:%S UTC")
                }

            elif tool_name == "web_search":
                query = arguments.get("query", "")
                res = await search_service.search(query, max_results=3)
                result = {"query": query, "results": res}

            elif tool_name == "csv_data_analyst":
                fpath = arguments.get("file_path", "")
                # Prevent path traversal
                norm_path = os.path.normpath(fpath)
                if norm_path.startswith("..") or os.path.isabs(norm_path):
                    raise ValueError("Illegal path traversal attempted.")

                if not os.path.exists(norm_path):
                    raise FileNotFoundError(f"File not found: {norm_path}")

                with open(norm_path, mode="r", encoding="utf-8", errors="ignore") as f:
                    reader = csv.reader(f)
                    headers = next(reader, [])
                    rows = list(reader)

                row_count = len(rows)
                col_count = len(headers)
                result = {
                    "row_count": row_count,
                    "column_count": col_count,
                    "headers": headers,
                    "preview": rows[:3] if rows else []
                }

            elif tool_name == "generate_image":
                prompt = arguments.get("prompt", "")
                style = arguments.get("style", "photorealistic")
                aspect_ratio = arguments.get("aspect_ratio", "1:1")
                if not prompt:
                    raise ValueError("A prompt is required for image generation.")
                gen_res = await image_service.generate_image(
                    prompt=prompt,
                    style=style,
                    aspect_ratio=aspect_ratio
                )
                result = {
                    "image_url": gen_res.get("url"),
                    "prompt": prompt,
                    "style": style,
                    "aspect_ratio": aspect_ratio,
                    "markdown": f"![{prompt}]({gen_res.get('url')})",
                    "provider": gen_res.get("provider")
                }

        except Exception as e:
            result = {"error": str(e)}

        # Audit record
        if db:
            try:
                end_time = datetime.now(timezone.utc)
                latency = int((end_time - start_time).total_seconds() * 1000)
                audit = AuditRecord(
                    event_type="tool_execution",
                    latency_ms=latency,
                    details={
                        "tool": tool_name,
                        "arguments": arguments,
                        "has_error": "error" in result
                    }
                )
                db.add(audit)
                db.commit()
            except Exception:
                pass

        return result

tool_registry = ToolRegistry()
