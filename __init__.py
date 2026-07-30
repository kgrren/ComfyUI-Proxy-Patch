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

        # JSON / ボディの取得
        try:
            data = await request.json()
            content = json.dumps(data, indent=2).encode("utf-8")
        except Exception:
            content = await request.read()

        if not content:
            print(f"[ProxyPatch Python] Warning: Received empty content for {filename}")
            return aiohttp.web.Response(status=400, text="Empty payload")

        user_dir = getattr(PromptServer.instance, "user_dir", "./user")
        save_path = os.path.join(user_dir, "default", filename)
        os.makedirs(os.path.dirname(save_path), exist_ok=True)

        with open(save_path, "wb") as f:
            f.write(content)

        print(f"[ProxyPatch Python] Saved file successfully ({len(content)} bytes): {save_path}")
        return aiohttp.web.json_response({"name": filename, "path": filename})
    except Exception as e:
        print(f"[ProxyPatch Python] Save error: {e}")
        return aiohttp.web.Response(status=500, text=str(e))

# --- 2. 一覧取得 ＆ 個別ファイル取得ハンドラー (GET) ---
async def handle_userdata_get(request):
    try:
        user_dir = getattr(PromptServer.instance, "user_dir", "./user")
        target_dir = os.path.join(user_dir, "default", "workflows")
        
        filename = request.match_info.get("filename", "")

        # A. 個別 JSON ファイルの取得リクエストの場合
        if filename:
            file_path = os.path.join(user_dir, "default", filename)
            if not os.path.exists(file_path):
                file_path = os.path.join(target_dir, filename)

            if os.path.exists(file_path) and os.path.getsize(file_path) > 0:
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        data = json.load(f)
                    print(f"[ProxyPatch Python] Served file: {file_path}")
                    return aiohttp.web.json_response(data)
                except Exception as json_err:
                    print(f"[ProxyPatch Python] Corrupted JSON skipped: {file_path} ({json_err})")
                    return aiohttp.web.Response(status=500, text="Corrupted JSON file")
            else:
                print(f"[ProxyPatch Python] File not found or empty: {file_path}")
                return aiohttp.web.Response(status=404, text="File not found or empty")

        # B. ワークフロー一覧のリクエストの場合
        files = []
        if os.path.exists(target_dir):
            for root, _, filenames in os.walk(target_dir):
                for f in filenames:
                    if f.endswith(".json"):
                        full_path = os.path.join(root, f)
                        # 空ファイル(0バイト)は一覧から除外
                        if os.path.getsize(full_path) == 0:
                            continue
                        
                        rel_path = os.relpath(full_path, target_dir).replace("\\", "/")
                        stat = os.stat(full_path)
                        
                        files.append({
                            "path": rel_path,
                            "name": f,
                            "mtime": stat.st_mtime,
                            "size": stat.st_size
                        })

        print(f"[ProxyPatch Python] Fetched {len(files)} valid workflows list for Vue UI")
        return aiohttp.web.json_response(files)
    except Exception as e:
        print(f"[ProxyPatch Python] Get error: {e}")
        return aiohttp.web.Response(status=500, text=str(e))

# ルートの登録
try:
    app = PromptServer.instance.app
    app.router.add_get("/api/proxy_patch/userdata/workflows", handle_userdata_get)
    app.router.add_get("/api/proxy_patch/userdata/{filename:.+}", handle_userdata_get)
    app.router.add_post("/api/proxy_patch/userdata/{filename:.+}", handle_userdata_post)
    print("[ProxyPatch Python] Registered full CRUD endpoints with fail-safe logic.")
except Exception as e:
    print(f"[ProxyPatch Python] Failed to register endpoints: {e}")

NODE_CLASS_MAPPINGS = {}
NODE_DISPLAY_NAME_MAPPINGS = {}
