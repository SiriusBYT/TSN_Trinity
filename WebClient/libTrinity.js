/* Sirio Network API*/
function SirioAPI(API_Request) {
    return new Promise(function(Success) {
        const Trinity = new WebSocket("wss://trinity.sirio-network.com");
        // const Trinity = new WebSocket("wss://localhost");
        Trinity.onopen = function(e) {
            log(`[SN-API] Sending Request "${API_Request}"`)
            Trinity.send(API_Request);
        };

        Trinity.onmessage = function(event) {
            Success(event.data);
        };

        Trinity.onclose = function(event) {
            if (event.wasClean) {
                log(`[SN-API] Connection closed. Code=${event.code} Reason=${event.reason}`);
                return "CLOSED";
            } else {
                log("[SN-API] Connection closed forcefully.");
                return "CLOSED_FORCE";
            };
        };

        Trinity.onerror = function(error) {
            log("[SN-API] Unknown error")
        };
    });
};