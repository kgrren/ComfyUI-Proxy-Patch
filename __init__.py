import os
import json
import time
import aiohttp.web
from server import PromptServer

WEB_DIRECTORY = "./web"

def get_base_user_dir():
    try:
        user_dir = getattr(PromptServer.instance, "user_dir", None)
        if user_dir and os.path.isabs(user_dir):
            return user_dir
    except Exception:
        pass
    return os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "user"))

# --- ワークフロー一覧 (.index.json) の動的生成 ---
def build_workflow_index(target_dir):
    files = []
    if os.path.exists(target_dir):
        for root, _, filenames in os.walk(target_dir):
            for f in filenames:
                if f.endswith(".json") and f != ".index.json":
                    full_path = os.path.join(root, f)
                    if os.path.getsize(full_path) == 0:
                        continue
                    
                    # os.path.relpath に修正
                    rel_path = os.path.relpath(full_path, target_dir).replace("\\", "/")
                    stat = os.stat(full_path)
                    
                    files.append({
                        "path": rel_path,
                        "name": f,
                        "mtime": stat.st_mtime * 1000,
                        "size": stat.st_size
                    })
    return files

# --- 1. 保存ハンドラー (POST) ---
async def handle_userdata_post(request):
    try:
        filename = request.match_info.get("filename", "")
        if not filename:
            return aiohttp.web.Response(status=400, text="Filename is required")

        try:
            data = await request.json()
            content = json.dumps(data, indent=2).encode("utf-8")
        except Exception:
            content = await request.read()

        if not content:
            return aiohttp.web.Response(status=400, text="Empty payload")

        base_user = get_base_user_dir()
        save_path = os.path.abspath(os.path.join(base_user, "default", filename))
        os.makedirs(os.path.dirname(save_path), exist_ok=True)

        with open(save_path, "wb") as f:
            f.write(content)

        print(f"[ProxyPatch Python] Saved file ({len(content)} bytes): {save_path}")
        return aiohttp.web.json_response({"name": filename, "path": filename})
    except Exception as e:
        print(f"[ProxyPatch Python] Save error: {e}")
        return aiohttp.web.Response(status=500, text=str(e))

# --- 2. 一覧 & 個別ファイル取得ハンドラー (GET) ---
async def handle_single_file_get(request):
    try:
        filename = request.match_info.get("filename", "")
        base_user = get_base_user_dir()
        target_dir = os.path.join(base_user, "default", "workflows")

        # インデックスファイル (.index.json) の要求時は動的に一覧を出力
        if filename in ["workflows/.index.json", ".index.json", "workflows"]:
            index_data = build_workflow_index(target_dir)
            print(f"[ProxyPatch Python] Served dynamic .index.json with {len(index_data)} workflows")
            return aiohttp.web.json_response(index_data)

        # 通常ファイルの探索
        candidates = [
            os.path.abspath(os.path.join(base_user, "default", filename)),
            os.path.abspath(os.path.join(target_dir, filename)),
            os.path.abspath(os.path.join(base_user, "default", filename.replace("workflows/", "")))
        ]

        target_file = None
        for path in candidates:
            if os.path.exists(path) and os.path.isfile(path) and os.path.getsize(path) > 0:
                target_file = path
                break

        if target_file:
            with open(target_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            print(f"[ProxyPatch Python] Served file: {target_file}")
            return aiohttp.web.json_response(data)
        else:
            print(f"[ProxyPatch Python] File not found: {filename}")
            return aiohttp.web.Response(status=404, text="File not found")
    except Exception as e:
        print(f"[ProxyPatch Python] GET error: {e}")
        return aiohttp.web.Response(status=500, text=str(e))

# --- 3. ユーザー認証エラー回避ハンドラー ---
async def handle_users_get(request):
    return aiohttp.web.json_response({
        "storage": "local",
        "users": {"default": "default"},
        "user": "default"
    })

# ルート登録
try:
    app = PromptServer.instance.app
    app.router.add_get("/api/proxy_patch/users", handle_users_get)
    app.router.add_get("/api/proxy_patch/userdata/{filename:.+}", handle_single_file_get)
    app.router.add_post("/api/proxy_patch/userdata/{filename:.+}", handle_userdata_post)
    print("[ProxyPatch Python] Fixed os.path.relpath and registered endpoints successfully.")
except Exception as e:
    print(f"[ProxyPatch Python] Failed to register endpoints: {e}")

NODE_CLASS_MAPPINGS = {}
NODE_DISPLAY_NAME_MAPPINGS = {}
