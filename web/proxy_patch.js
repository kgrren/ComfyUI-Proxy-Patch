import { app } from "../../scripts/app.js";

(function () {
    const pathname = window.location.pathname;
    // "/proxy/8188/" から末尾のスラッシュを除いたベースパスを取得
    const basePath = pathname.endsWith("/") ? pathname.slice(0, -1) : pathname;

    if (!basePath) return;

    console.log(`[ProxyPatch] Subpath detected: "${basePath}". Patching fetch, XHR, and WebSocket...`);

    // 1. fetch のパッチ
    const originalFetch = window.fetch;
    window.fetch = async function (input, init) {
        if (typeof input === "string") {
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

    // 2. XMLHttpRequest (XHR) のパッチ（保存処理などで使われる場合対策）
    const originalOpen = XMLHttpRequest.prototype.open;
    XMLHttpRequest.prototype.open = function (method, url, ...args) {
        if (typeof url === "string" && url.startsWith("/") && !url.startsWith(basePath)) {
            url = basePath + url;
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
