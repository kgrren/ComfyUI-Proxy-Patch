import { app } from "../../scripts/app.js";

(function () {
    const pathname = window.location.pathname;
    const basePath = pathname.endsWith("/") ? pathname.slice(0, -1) : pathname;

    if (!basePath) return;

    console.log(`[ProxyPatch] Subpath detected: "${basePath}". Patching fetch, XHR, and WebSocket...`);

    // 1. fetch のパッチ
    const originalFetch = window.fetch;
    window.fetch = async function (input, init) {
        let url = typeof input === "string" ? input : (input instanceof Request ? input.url : "");

        if (url) {
            // A. サブパスの補正
            if (url.startsWith("/") && !url.startsWith(basePath)) {
                url = basePath + url;
            }

            // B. 405エラー回避: /api/userdata/workflows%2Fxxx.json の %2F によるプロキシ破壊を迂回
            // パスにエンコードされたスラッシュが含まれている場合、プロキシが誤解読するためパラメータ構造を補正
            if (url.includes("/api/userdata/") && url.includes("%2F")) {
                console.log(`[ProxyPatch] Intercepting userdata API: ${url}`);
                // %2F を安全なデコード状態に処理
                url = url.replace(/%2F/g, "/");
            }

            if (typeof input === "string") {
                input = url;
            } else if (input instanceof Request) {
                input = new Request(url, input);
            }
        }
        return originalFetch.call(this, input, init);
    };

    // 2. XMLHttpRequest (XHR) のパッチ
    const originalOpen = XMLHttpRequest.prototype.open;
    XMLHttpRequest.prototype.open = function (method, url, ...args) {
        if (typeof url === "string") {
            if (url.startsWith("/") && !url.startsWith(basePath)) {
                url = basePath + url;
            }
            if (url.includes("/api/userdata/") && url.includes("%2F")) {
                url = url.replace(/%2F/g, "/");
            }
        }
        return originalOpen.call(this, method, url, ...args);
    };

    // 3. WebSocket のパッチ
    const OriginalWebSocket = window.WebSocket;
    window.WebSocket = function (url, protocols) {
        try {
            const parsedUrl = new URL(url);
            if (parsedUrl.pathname.startsWith("/") && !parsedUrl.pathname.startsWith(basePath)) {
                parsedUrl.pathname = basePath + parsedUrl.pathname;
                url = parsedUrl.toString();
            }
        } catch (e) {}
        return new OriginalWebSocket(url, protocols);
    };
    window.WebSocket.prototype = OriginalWebSocket.prototype;
})();

app.registerExtension({
    name: "ComfyUI.ProxyPatch",
    async setup() {
        console.log("[ProxyPatch] Extension loaded successfully.");
    }
});
