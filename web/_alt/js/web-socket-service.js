const WebSocketService = (() => {
    let socket = null;
    let onMessageCallback = null; // Wird vom uiManager/main gesetzt

    const WS_URL = `ws://${window.location.hostname}:8765/ws`; // Annahme: Server läuft auf gleichem Host, Port 8765

    function connect(playerName, tableName, sessionId = null) {
        return new Promise((resolve, reject) => {
            let url = WS_URL;
            if (sessionId) {
                url += `?session_id=${sessionId}`;
            }
            else if (playerName && tableName) {
                url += `?player_name=${encodeURIComponent(playerName)}&table_name=${encodeURIComponent(tableName)}`;
            }
            else {
                reject("Spielername und Tischname oder Session-ID benötigt.");
                return;
            }

            console.log(`Versuche Verbindung zu: ${url}`);
            socket = new WebSocket(url);

            socket.onopen = () => {
                console.log("WebSocket-Verbindung erfolgreich hergestellt.");
                resolve();
            };

            socket.onmessage = (event) => {
                try {
                    const message = JSON.parse(event.data);
                    console.log("Nachricht vom Server empfangen:", message);
                    if (onMessageCallback) {
                        onMessageCallback(message);
                    }
                } catch (e) {
                    console.error("Fehler beim Parsen der Server-Nachricht:", e, event.data);
                }
            };

            socket.onerror = (error) => {
                console.error("WebSocket-Fehler:", error);
                reject(error);
            };

            socket.onclose = (event) => {
                console.log("WebSocket-Verbindung geschlossen:", event.code, event.reason);
                socket = null;
                // Hier könnte man Logik für Reconnect-Versuche einbauen oder den Nutzer informieren
            };
        });
    }

    function sendMessage(type, payload = {}) {
        if (socket && socket.readyState === WebSocket.OPEN) {
            const message = {type, payload};
            console.log("Sende Nachricht an Server:", message);
            socket.send(JSON.stringify(message));
        }
        else {
            console.warn("WebSocket nicht offen. Nachricht nicht gesendet:", type, payload);
        }
    }

    function setOnMessageCallback(callback) {
        onMessageCallback = callback;
    }

    function closeConnection() {
        if (socket) {
            socket.close();
        }
    }

    function isConnected() {
        return socket && socket.readyState === WebSocket.OPEN;
    }

    return {
        connect,
        sendMessage,
        setOnMessageCallback,
        closeConnection,
        isConnected
    };
})();