import os
import json
import time
import aiohttp.web
from server import PromptServer

WEB_DIRECTORY = "./web"

# --- 1. 保存ハンドラー (POST) ---
async def handle_userdata_post(request):
    try:
        filename = request.match_info.get("filename", "")
        if not filename:
            return aiohttp.web.Response(status=400, text="Filename is required")

        body = await request.read()
        user_dir = getattr(PromptServer.instance, "user_dir", "./user")
        
        save_path = os.path.join(user_dir, "default", filename)
        os.makedirs(os.path.dirname(save_path), exist_ok=True)

        with open(save_path, "wb") as f:
            f.write(body)

        print(f"[ProxyPatch Python] Saved file: {save_path}")
        # ComfyUI Vue UI が期待するレスポンス
        return aiohttp.web.json_response({"name": filename, "path": filename})
    except Exception as e:
        print(f"[ProxyPatch Python] Save error: {e}")
        return aiohttp.web.Response(status=500, text=str(e))

# --- 2. 一覧取得ハンドラー (GET) ---
async def handle_userdata_get(request):
    try:
        user_dir = getattr(PromptServer.instance, "user_dir", "./user")
        target_dir = os.path.join(user_dir, "default", "workflows")
        
        files = []
        if os.path.exists(target_dir):
            for root, _, filenames in os.walk(target_dir):
                for f in filenames:
                    if f.endswith(".json"):
                        full_path = os.path.join(root, f)
                        rel_path = os.relpath(full_path, target_dir).replace("\\", "/")
                        stat = os.stat(full_path)
                        
                        # ComfyUI Vue UI (V2) が期待するオブジェクト形式
                        files.append({
                            "path": rel_path,
                            "name": f,
                            "mtime": stat.st_mtime,
                            "size": stat.st_size
                        })

        print(f"[ProxyPatch Python] Fetched {len(files)} workflows for Vue UI")
        return aiohttp.web.json_response(files)
    except Exception as e:
        print(f"[ProxyPatch Python] Get list error: {e}")
        return aiohttp.web.json_response([])

# ルートの登録
try:
    app = PromptServer.instance.app
    app.router.add_post("/api/proxy_patch/userdata/{filename:.+}", handle_userdata_post)
    app.router.add_get("/api/proxy_patch/userdata/workflows", handle_userdata_get)
    print("[ProxyPatch Python] Registered POST & GET endpoints for Vue UI.")
except Exception as e:
    print(f"[ProxyPatch Python] Failed to register endpoints: {e}")

NODE_CLASS_MAPPINGS = {}
NODE_DISPLAY_NAME_MAPPINGS = {}
