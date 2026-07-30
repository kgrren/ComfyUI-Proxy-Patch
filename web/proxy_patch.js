import { app } from "../../scripts/app.js";

(function () {
    const pathname = window.location.pathname;
    const basePath = pathname.endsWith("/") ? pathname.slice(0, -1) : pathname;

    if (!basePath) return;

    console.log(`[ProxyPatch] Subpath detected: "${basePath}". Active.`);

    const originalFetch = window.fetch;
    window.fetch = async function (input, init = {}) {
        let url = typeof input === "string" ? input : (input instanceof Request ? input.url : "");
        let method = init.method || (input instanceof Request ? input.method : "GET");

        if (url) {
            // A. ユーザー一覧リクエスト（KeyError 回避）
            if (url.includes("/api/users") && method.toUpperCase() === "GET") {
                url = `${basePath}/api/proxy_patch/users`;
            }
            // B. ワークフロー一覧取得 (GET /api/userdata/workflows)
            else if (url.includes("/api/userdata/workflows") && method.toUpperCase() === "GET" && !url.includes(".json")) {
                url = `${basePath}/api/proxy_patch/userdata/workflows`;
                console.log(`[ProxyPatch] Redirected GET workflows list to: ${url}`);
            }
            // C. ファイル保存 (POST/PUT /api/userdata/...)
            else if (url.includes("/api/userdata/") && (method.toUpperCase() === "POST" || method.toUpperCase() === "PUT")) {
                let cleanPath = url.split("/api/userdata/")[1] || "";
                cleanPath = cleanPath.replace(/%2F/g, "/");
                
                url = `${basePath}/api/proxy_patch/userdata/${cleanPath}`;
                init.method = "POST";
                console.log(`[ProxyPatch] Redirected POST/PUT save to: ${url}`);
            }
            // D. 個別ファイル取得 (GET /api/userdata/...)
            else if (url.includes("/api/userdata/") && method.toUpperCase() === "GET") {
                let cleanPath = url.split("/api/userdata/")[1] || "";
                cleanPath = cleanPath.replace(/%2F/g, "/");
                
                url = `${basePath}/api/proxy_patch/userdata/${cleanPath}`;
                console.log(`[ProxyPatch] Redirected GET single file to: ${url}`);
            }
            // E. サブパス補正
            else if (url.startsWith("/") && !url.startsWith(basePath)) {
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

    // WebSocket パッチ
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
