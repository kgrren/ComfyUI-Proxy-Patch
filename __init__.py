import aiohttp.web
from server import PromptServer

WEB_DIRECTORY = "./web"

# ComfyUI の既存ルートに割込パッチを適用
try:
    routes = PromptServer.instance.app.router

    # ユーザーデータ保存用ハンドラー（PUT処理）を探して POST にも登録する
    userdata_handler = None
    for route in routes.routes():
        # /api/userdata/{file:.+} の PUT ハンドラーを取得
        if "/api/userdata" in route.resource.canonical and route.method == "PUT":
            userdata_handler = route.handler
            break

    if userdata_handler:
        # POST リクエストでも PUT と同じ保存処理を実行するようにルートを追加
        routes.add_post("/api/userdata/{file:.+}", userdata_handler)
        print("[ProxyPatch Python] Successfully registered POST fallback for /api/userdata/")
    else:
        print("[ProxyPatch Python] Warning: Could not find PUT handler for /api/userdata")

except Exception as e:
    print(f"[ProxyPatch Python] Error applying route patch: {e}")

NODE_CLASS_MAPPINGS = {}
NODE_DISPLAY_NAME_MAPPINGS = {}
