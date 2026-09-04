const [requestType, requestDataJson = "{}"] = process.argv.slice(2);

if (!requestType) {
  throw new Error("Usage: node scripts/obs-control.mjs <RequestType> [requestDataJson]");
}

const requestData = JSON.parse(requestDataJson);
const requestId = `${requestType}-${Date.now()}`;
const socket = new WebSocket("ws://127.0.0.1:4455");

const timeout = setTimeout(() => {
  socket.close();
  throw new Error(`OBS request timed out: ${requestType}`);
}, 15_000);

socket.addEventListener("message", (event) => {
  const message = JSON.parse(String(event.data));

  if (message.op === 0) {
    socket.send(JSON.stringify({ op: 1, d: { rpcVersion: 1 } }));
    return;
  }

  if (message.op === 2) {
    socket.send(JSON.stringify({
      op: 6,
      d: { requestType, requestId, requestData },
    }));
    return;
  }

  if (message.op === 7 && message.d?.requestId === requestId) {
    clearTimeout(timeout);
    console.log(JSON.stringify(message.d));
    socket.close();
  }
});

socket.addEventListener("error", (event) => {
  clearTimeout(timeout);
  throw event.error ?? new Error("Could not connect to OBS WebSocket");
});
