import { app } from "../../scripts/app.js";

(function () {
    const pathname = window.location.pathname;
    const basePath = pathname.endsWith("/") ? pathname.slice(0, -1) : pathname;

    if (!basePath) return;

    console.log(`[ProxyPatch] Subpath detected: "${basePath}". Patching fetch, XHR, and WebSocket...`);

    // URL補正ヘルパー（サブパス付与 ＆ %2F のパッチ）
    function patchUrl(urlStr) {
        if (typeof urlStr !== "string") return urlStr;

        let patched = urlStr;

        // 1. サブパス(/proxy/8188)の付与
        if (patched.startsWith("/") && !patched.startsWith(basePath)) {
            patched = basePath + patched;
        }

        // 2. jupyter-server-proxy の 405 エラー原因となる %2F (workflows%2Fxxx.json) をデコードして標準の / に変換
        if (patched.includes("/api/userdata/") && patched.includes("%2F")) {
            console.log(`[ProxyPatch] Decoding %2F in userdata URL: ${patched}`);
            patched = patched.replace(/%2F/g, "/");
        }

        return patched;
    }

    // 1. fetch のオーバーライド
    const originalFetch = window.fetch;
    window.fetch = async function (input, init) {
        if (typeof input === "string") {
            input = patchUrl(input);
        } else if (input instanceof Request) {
            const patchedUrl = patchUrl(input.url);
            if (patchedUrl !== input.url) {
                input = new Request(patchedUrl, input);
            }
        }
        return originalFetch.call(this, input, init);
    };

    // 2. XMLHttpRequest (XHR) のオーバーライド
    const originalOpen = XMLHttpRequest.prototype.open;
    XMLHttpRequest.prototype.open = function (method, url, ...args) {
        if (typeof url === "string") {
            url = patchUrl(url);
        }
        return originalOpen.call(this, method, url, ...args);
    };

    // 3. WebSocket のオーバーライド
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
