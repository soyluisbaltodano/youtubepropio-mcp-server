from mcp.server.fastmcp import FastMCP
from mcp.server.transport_security import TransportSecuritySettings
from dotenv import load_dotenv
from pathlib import Path
import json

# Carga el .env desde la carpeta del servidor, sin importar desde dónde se ejecute
load_dotenv(Path(__file__).parent / ".env")

from youtube_data import get_channel_stats, search_youtube, get_channel_videos, get_video_details
from youtube_analytics import get_my_analytics, get_traffic_sources, get_top_videos_analytics
from google_trends import keyword_trends, trending_now, related_keywords, keyword_by_region
from youtube_extras import (
    get_video_transcript, get_channel_rss, get_video_comments,
    compare_channels, get_channel_playlists,
)

# Disable DNS rebinding protection so external hosts (Render.com) can connect
mcp = FastMCP(
    "youtube-mcp",
    transport_security=TransportSecuritySettings(enable_dns_rebinding_protection=False),
)


# ── YouTube Data (datos públicos de cualquier canal) ──────────────────────────

@mcp.tool()
def channel_stats(channel_id: str) -> str:
    """Estadísticas de cualquier canal: subs, vistas totales, cantidad de videos. Acepta @handle o channel ID."""
    return json.dumps(get_channel_stats(channel_id), ensure_ascii=False, indent=2)


@mcp.tool()
def search_videos(query: str, max_results: int = 10, search_type: str = "video") -> str:
    """
    Busca en YouTube. search_type: 'video', 'channel', 'playlist'.
    Útil para encontrar competencia o videos sobre un tema.
    """
    return json.dumps(search_youtube(query, max_results, search_type), ensure_ascii=False, indent=2)


@mcp.tool()
def channel_videos(channel_id: str, max_results: int = 20, order: str = "viewCount") -> str:
    """
    Videos de un canal con sus stats. order: 'viewCount' (más vistos) o 'date' (más recientes).
    Útil para analizar qué funciona en canales de la competencia.
    """
    return json.dumps(get_channel_videos(channel_id, max_results, order), ensure_ascii=False, indent=2)


@mcp.tool()
def video_details(video_id: str) -> str:
    """Detalles completos de un video: vistas, likes, comentarios, duración, tags. Acepta ID o URL completa."""
    return json.dumps(get_video_details(video_id), ensure_ascii=False, indent=2)


# ── YouTube Analytics (solo mi canal, requiere OAuth) ─────────────────────────

@mcp.tool()
def my_analytics(start_date: str, end_date: str, metrics: str = "views,estimatedMinutesWatched,subscribersGained", dimensions: str = "day") -> str:
    """
    Analytics PRIVADOS de mi canal (abre navegador para autorizar la primera vez).
    start_date / end_date: YYYY-MM-DD
    metrics: views, estimatedMinutesWatched, subscribersGained, likes, comments, averageViewPercentage
    dimensions: day, country, deviceType, insightTrafficSourceType
    """
    return json.dumps(get_my_analytics(start_date, end_date, metrics, dimensions), ensure_ascii=False, indent=2)


@mcp.tool()
def traffic_sources(start_date: str, end_date: str) -> str:
    """De dónde vienen las vistas de mi canal: búsqueda YouTube, sugeridos, externos, inicio, etc."""
    return json.dumps(get_traffic_sources(start_date, end_date), ensure_ascii=False, indent=2)


@mcp.tool()
def top_videos_analytics(start_date: str, end_date: str, limit: int = 10) -> str:
    """Mis videos con mejor rendimiento en un período con vistas, watch time, retención promedio y subs ganados."""
    return json.dumps(get_top_videos_analytics(start_date, end_date, limit), ensure_ascii=False, indent=2)


# ── Google Trends (tendencias de búsqueda) ────────────────────────────────────

@mcp.tool()
def keyword_interest(keywords: str, country: str = "MX", timeframe: str = "today 3-m") -> str:
    """
    Interés de búsqueda en Google a lo largo del tiempo (0-100).
    keywords: palabras separadas por coma, máximo 5 (ej: 'bebé, maternidad, lactancia')
    country: MX, US, CO, AR, ES...
    timeframe: 'today 1-m', 'today 3-m', 'today 12-m', 'today 5-y'
    """
    kw_list = [k.strip() for k in keywords.split(",")][:5]
    return json.dumps(keyword_trends(kw_list, country, timeframe), ensure_ascii=False, indent=2)


@mcp.tool()
def trending_searches(country: str = "mexico") -> str:
    """
    Qué está buscando la gente AHORA MISMO en Google.
    country: 'mexico', 'united_states', 'colombia', 'argentina', 'spain'
    """
    return json.dumps(trending_now(country), ensure_ascii=False, indent=2)


@mcp.tool()
def related_queries(keyword: str, country: str = "MX") -> str:
    """Keywords relacionadas con un tema: las más buscadas y las que están subiendo rápido."""
    return json.dumps(related_keywords(keyword, country), ensure_ascii=False, indent=2)


@mcp.tool()
def interest_by_region(keyword: str, country: str = "MX") -> str:
    """En qué estados o regiones se busca más una palabra clave. Útil para saber dónde está tu audiencia."""
    return json.dumps(keyword_by_region(keyword, country), ensure_ascii=False, indent=2)


# ── Extras: transcripción, RSS, comentarios, comparación, playlists ──────────

@mcp.tool()
def video_transcript(video_id: str, language: str = "es") -> str:
    """
    Transcripción completa de un video de YouTube. No requiere API key.
    Acepta ID o URL completa. language: 'es', 'en', etc.
    Si no hay transcripción en el idioma pedido, usa la que esté disponible.
    """
    return json.dumps(get_video_transcript(video_id, language), ensure_ascii=False, indent=2)


@mcp.tool()
def channel_rss_feed(channel_id: str, max_results: int = 15) -> str:
    """
    Últimos videos de un canal via RSS — sin consumir quota de la API de YouTube.
    Ideal para monitorear competencia. Acepta @handle o channel ID.
    """
    return json.dumps(get_channel_rss(channel_id, max_results), ensure_ascii=False, indent=2)


@mcp.tool()
def video_comments(video_id: str, max_results: int = 20, order: str = "relevance") -> str:
    """
    Comentarios top de un video. Revela qué le importa a la audiencia.
    order: 'relevance' (más relevantes) o 'time' (más recientes).
    Acepta ID o URL completa.
    """
    return json.dumps(get_video_comments(video_id, max_results, order), ensure_ascii=False, indent=2)


@mcp.tool()
def compare_channels_tool(channels: str) -> str:
    """
    Compara 2-4 canales lado a lado: subs, vistas, videos, promedio de vistas por video.
    channels: handles o IDs separados por coma (ej: '@missmaru, @otrocanal, @tercero')
    """
    channel_list = [c.strip() for c in channels.split(",")][:4]
    return json.dumps(compare_channels(channel_list), ensure_ascii=False, indent=2)


@mcp.tool()
def channel_playlists(channel_id: str, max_results: int = 20) -> str:
    """
    Playlists de un canal ordenadas por cantidad de videos.
    Acepta @handle o channel ID.
    """
    return json.dumps(get_channel_playlists(channel_id, max_results), ensure_ascii=False, indent=2)


def build_http_app():
    import uuid
    from starlette.requests import Request
    from starlette.responses import JSONResponse, HTMLResponse, RedirectResponse
    from starlette.middleware.base import BaseHTTPMiddleware
    from starlette.middleware.cors import CORSMiddleware

    mcp_asgi = mcp.streamable_http_app()

    class OAuthMiddleware(BaseHTTPMiddleware):
        async def dispatch(self, request: Request, call_next):
            path = request.url.path

            if path == "/.well-known/oauth-authorization-server":
                base = str(request.base_url).rstrip("/")
                return JSONResponse({
                    "issuer": base,
                    "authorization_endpoint": f"{base}/oauth/authorize",
                    "token_endpoint": f"{base}/oauth/token",
                    "registration_endpoint": f"{base}/oauth/register",
                    "response_types_supported": ["code"],
                    "grant_types_supported": ["authorization_code"],
                    "code_challenge_methods_supported": ["S256"],
                })

            if path == "/oauth/register":
                body = await request.json()
                return JSONResponse({
                    "client_id": str(uuid.uuid4()),
                    "client_secret": str(uuid.uuid4()),
                    "redirect_uris": body.get("redirect_uris", []),
                    "grant_types": ["authorization_code"],
                    "response_types": ["code"],
                    "token_endpoint_auth_method": "client_secret_post",
                }, status_code=201)

            if path == "/oauth/authorize":
                if request.method == "GET":
                    p = request.query_params
                    redirect_uri = p.get("redirect_uri", "")
                    state = p.get("state", "")
                    code = str(uuid.uuid4())
                    html = f"""<!DOCTYPE html>
<html><head><meta charset="utf-8"><title>Autorizar YouTube MCP</title>
<style>
  body{{font-family:-apple-system,Arial,sans-serif;max-width:420px;margin:80px auto;padding:20px;background:#f8fafc;text-align:center}}
  .card{{background:white;padding:40px;border-radius:12px;box-shadow:0 2px 12px rgba(0,0,0,.08)}}
  h2{{color:#1e293b}} p{{color:#64748b;margin-bottom:28px}}
  button{{background:#2563eb;color:white;padding:12px 32px;border:none;border-radius:8px;font-size:16px;cursor:pointer;width:100%}}
  button:hover{{background:#1d4ed8}}
</style></head>
<body><div class="card">
  <div style="font-size:48px;margin-bottom:16px">🎬</div>
  <h2>YouTube MCP</h2>
  <p>Claude Desktop quiere conectarse a tu servidor de análisis de YouTube.</p>
  <form method="post">
    <input type="hidden" name="redirect_uri" value="{redirect_uri}">
    <input type="hidden" name="state" value="{state}">
    <input type="hidden" name="code" value="{code}">
    <button type="submit">✅ Autorizar acceso</button>
  </form>
</div></body></html>"""
                    return HTMLResponse(html)
                form = await request.form()
                redirect_uri = form.get("redirect_uri", "")
                state = form.get("state", "")
                code = form.get("code", str(uuid.uuid4()))
                sep = "&" if "?" in redirect_uri else "?"
                return RedirectResponse(f"{redirect_uri}{sep}code={code}&state={state}", status_code=302)

            if path == "/oauth/token":
                return JSONResponse({
                    "access_token": str(uuid.uuid4()),
                    "token_type": "bearer",
                    "expires_in": 31536000,
                })

            return await call_next(request)

    # OAuth middleware envuelve el MCP SSE app
    app = OAuthMiddleware(mcp_asgi)
    app = CORSMiddleware(app, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])
    return app


if __name__ == "__main__":
    import sys
    import os

    port = int(os.getenv("PORT", 8000))
    http_mode = "--http" in sys.argv or "PORT" in os.environ

    if http_mode:
        import uvicorn
        uvicorn.run(build_http_app(), host="0.0.0.0", port=port)
    else:
        mcp.run()
