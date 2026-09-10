/** Vite middleware: POST /api/lseg → python bridge. Bypasses TanStack server fns. */

function readBody(req) {
  return new Promise((resolve, reject) => {
    const chunks = [];
    req.on("data", (c) => chunks.push(c));
    req.on("end", () => resolve(Buffer.concat(chunks).toString("utf8")));
    req.on("error", reject);
  });
}

function timeoutFor(op) {
  if (op === "history" || op === "options_fetch") return 180000;
  if (op === "search") return 30000;
  if (op === "health") return 8000;
  return 20000;
}

export function lsegApiPlugin() {
  return {
    name: "lseg-api",
    apply: "serve",
    configureServer(server) {
      server.middlewares.use(async (req, res, next) => {
        const pathOnly = (req.url ?? "").split("?", 1)[0];
        if (pathOnly !== "/api/lseg") {
          next();
          return;
        }
        if ((req.method ?? "GET").toUpperCase() !== "POST") {
          res.statusCode = 405;
          res.end("POST only");
          return;
        }
        try {
          const raw = await readBody(req);
          const payload = JSON.parse(raw || "{}");
          const mod = await server.ssrLoadModule("/src/lib/lseg.server.ts");
          const result = await mod.runBridge(payload, timeoutFor(payload.op));
          res.statusCode = 200;
          res.setHeader("Content-Type", "application/json");
          res.end(JSON.stringify(result ?? { ok: false, code: "upstream", message: "empty" }));
        } catch (error) {
          const message = error instanceof Error ? error.message : String(error);
          res.statusCode = 200;
          res.setHeader("Content-Type", "application/json");
          res.end(
            JSON.stringify({
              ok: false,
              code: "upstream",
              message,
            }),
          );
        }
      });
    },
  };
}
