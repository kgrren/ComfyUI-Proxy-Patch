import os
import folder_paths
from aiohttp import web
from server import PromptServer

# webディレクトリの絶対パスを取得
WEB_DIRECTORY = os.path.join(os.path.dirname(__file__), "web")

NODE_CLASS_MAPPINGS = {}
NODE_DISPLAY_NAME_MAPPINGS = {}

# ComfyUI の web サーバー (aiohttp) にミドルウェアフックを挿入
try:
    app = PromptServer.instance.app

    @web.middleware
    async def proxy_header_middleware(request, handler):
        # jupyter-server-proxy 等で 405 になるリクエストヘッダーの補正
        # OPTIONS リクエスト（Preflight）が飛んできた場合に 200 OK を返して通過させる
        if request.method == "OPTIONS":
            response = web.Response(status=200)
            response.headers["Access-Control-Allow-Origin"] = "*"
            response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"
            response.headers["Access-Control-Allow-Headers"] = "*"
            return response

        try:
            response = await handler(request)
            return response
        except web.HTTPMethodNotAllowed:
            # メソッド不一致による 405 をレスポンスヘッダー補正でフォールバック
            return web.Response(status=200, text="{}")

    # ミドルウェアを追加
    app.middlewares.append(proxy_header_middleware)
    print("[ProxyPatch] Python middleware hook applied successfully.")

except Exception as e:
    print(f"[ProxyPatch] Failed to apply python middleware hook: {e}")

__all__ = ["NODE_CLASS_MAPPINGS", "NODE_DISPLAY_NAME_MAPPINGS", "WEB_DIRECTORY"]
