import { app } from "../../scripts/app.js";

(function () {
    const pathname = window.location.pathname;
    const basePath = pathname.endsWith("/") ? pathname.slice(0, -1) : pathname;

    if (!basePath) return;

    console.log(`[ProxyPatch] Subpath detected: "${basePath}". Active.`);

    // 1. fetch のパッチ
    const originalFetch = window.fetch;
    window.fetch = async function (input, init = {}) {
        let url = typeof input === "string" ? input : (input instanceof Request ? input.url : "");

        if (url) {
            // A. userdata API の横取りとカスタム POST エンドポイントへの転送
            if (url.includes("/api/userdata/")) {
                // 例: .../api/userdata/workflows%2Ftxt2img.json 
                // -> .../api/proxy_patch/userdata/workflows/txt2img.json
                let cleanPath = url.split("/api/userdata/")[1] || "";
                cleanPath = cleanPath.replace(/%2F/g, "/");
                
                url = `${basePath}/api/proxy_patch/userdata/${cleanPath}`;
                init.method = "POST";
                console.log(`[ProxyPatch] Redirected userdata save request to: ${url}`);
            } else if (url.startsWith("/") && !url.startsWith(basePath)) {
                // 通常のサブパス補正
                url = basePath + url;
            }

            if (typeof input === "string") {
                input = url;
            } else if (input instanceof Request) {
                input = new Request(url, {
                    ...input,
                    method: init.method || input.method
                });
            }
        }
        return originalFetch.call(this, input, init);
    };

    // 2. WebSocket のパッチ
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
