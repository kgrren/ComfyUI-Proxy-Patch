import os
import json
import aiohttp.web
from server import PromptServer

WEB_DIRECTORY = "./web"

# ComfyUI のユーザーデータ保存ロジックを直呼び出すカスタム POST ハンドラー
async def handle_userdata_post(request):
    try:
        # URL パスからファイル名/相対パスを取得 (/api/proxy_patch/userdata/xxxx)
        filename = request.match_info.get("filename", "")
        if not filename:
            return aiohttp.web.Response(status=400, text="Filename is required")

        # リクエストボディの取得
        body = await request.read()

        # ComfyUIのユーザーデータディレクトリ（通常は user/default/ など）に安全に保存
        # PromptServer の user_manager または直接ファイル保存
        user_dir = getattr(PromptServer.instance, "user_dir", "./user")
        
        # 保存先パスの構築 (workflows/xxx.json など)
        save_path = os.path.join(user_dir, "default", filename)
        os.makedirs(os.path.dirname(save_path), exist_ok=True)

        with open(save_path, "wb") as f:
            f.write(body)

        print(f"[ProxyPatch Python] Successfully saved file via custom endpoint: {save_path}")
        return aiohttp.web.json_response({"status": "success", "path": save_path})

    except Exception as e:
        print(f"[ProxyPatch Python] Save error: {e}")
        return aiohttp.web.Response(status=500, text=str(e))

# 専用ルートの登録
try:
    app = PromptServer.instance.app
    app.router.add_post("/api/proxy_patch/userdata/{filename:.+}", handle_userdata_post)
    print("[ProxyPatch Python] Registered endpoint: POST /api/proxy_patch/userdata/{filename:.+}")
except Exception as e:
    print(f"[ProxyPatch Python] Failed to register endpoint: {e}")

NODE_CLASS_MAPPINGS = {}
NODE_DISPLAY_NAME_MAPPINGS = {}
