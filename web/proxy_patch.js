import { app } from "../../scripts/app.js";

(function () {
    // 1. 現在のページの絶対パスからベースパス（サブパス）を取得
    // 例: "https://xxx.paperspace.com/proxy/8188/" -> "/proxy/8188"
    const pathname = window.location.pathname;
    const basePath = pathname.endsWith("/") ? pathname.slice(0, -1) : pathname;

    // ルート直下で動作している場合は何もしない
    if (!basePath) return;

    console.log(`[ProxyPatch] Subpath detected: "${basePath}". Patching fetch and WebSocket...`);

    // 2. 原義の fetch を保存してオーバーライド
    const originalFetch = window.fetch;
    window.fetch = async function (input, init) {
        if (typeof input === "string") {
            // "/api/..." や "/view" などのルート相対パスをサブパス配下に書き換え
            if (input.startsWith("/") && !input.startsWith(basePath)) {
                input = basePath + input;
            }
        } else if (input instanceof Request) {
            const url = new URL(input.url);
            if (url.origin === window.location.origin && url.pathname.startsWith("/") && !url.pathname.startsWith(basePath)) {
                const newUrl = basePath + url.pathname + url.search;
                input = new Request(newUrl, input);
            }
        }
        return originalFetch.call(this, input, init);
    };

    // 3. 原義の WebSocket を保存してオーバーライド
    const OriginalWebSocket = window.WebSocket;
    window.WebSocket = function (url, protocols) {
        try {
            const parsedUrl = new URL(url);
            // WebSocketのパスがサブパスを含んでいない場合に修正
            if (parsedUrl.pathname.startsWith("/") && !parsedUrl.pathname.startsWith(basePath)) {
                parsedUrl.pathname = basePath + parsedUrl.pathname;
                url = parsedUrl.toString();
            }
        } catch (e) {
            // URL解析エラー時はフォールバック
        }
        return new OriginalWebSocket(url, protocols);
    };
    window.WebSocket.prototype = OriginalWebSocket.prototype;
})();

// ComfyUI拡張機能として登録（拡張API用）
app.registerExtension({
    name: "ComfyUI.ProxyPatch",
    async setup() {
        console.log("[ProxyPatch] Extension loaded successfully.");
    }
});
