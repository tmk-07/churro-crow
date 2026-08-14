interface Env {
  API_ORIGIN: string;
}

export default {
  async fetch(request: Request, env: Env): Promise<Response> {
    const url = new URL(request.url);
    if (!url.pathname.startsWith("/api/")) {
      return new Response("Not found", { status: 404 });
    }
    if (!env.API_ORIGIN) {
      return Response.json(
        { detail: { message: "The calculation API has not been deployed yet.", issues: [] } },
        { status: 503 },
      );
    }
    const upstream = new URL(`${url.pathname}${url.search}`, env.API_ORIGIN);
    try {
      const response = await fetch(new Request(upstream, request));
      const contentType = response.headers.get("content-type") ?? "";
      if (!response.ok && !contentType.includes("application/json")) {
        return Response.json(
          { detail: { message: "The calculation API has not been deployed yet.", issues: [] } },
          { status: 503 },
        );
      }
      return response;
    } catch {
      return Response.json(
        { detail: { message: "The calculation API is temporarily unavailable.", issues: [] } },
        { status: 503 },
      );
    }
  },
};
