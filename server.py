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
from youtube_outliers import find_outliers

# Disable DNS rebinding protection so external hosts (Render.com) can connect
mcp = FastMCP(
    "youtube-mcp",
    stateless_http=True,
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


@mcp.tool()
def outlier_videos(
    niche: str,
    max_candidates: int = 25,
    min_score: float = 3.0,
    max_results: int = 15,
    published_after_days: int = None,
) -> str:
    """
    Encuentra videos "outlier" en un nicho: videos que superan por mucho (3x, 10x, 50x...)
    el promedio normal de SU PROPIO canal. Así se identifican formatos/temas que están
    funcionando ahora mismo, sin importar el tamaño del canal.
    niche: tema o palabra clave a buscar (ej: 'rutina bebé 6 meses', 'lactancia consejos')
    max_candidates: cuántos videos de búsqueda revisar (máx 50)
    min_score: multiplicador mínimo para considerar un video outlier (default 3x)
    max_results: cuántos outliers devolver, ordenados de mayor a menor score
    published_after_days: si se especifica, solo revisa videos publicados en los últimos N días
    """
    return json.dumps(
        find_outliers(niche, max_candidates, min_score, max_results, published_after_days),
        ensure_ascii=False, indent=2,
    )


def build_http_app():
    from mcp_oauth import build_protected_http_app
    return build_protected_http_app(
        mcp,
        server_label="YouTube MCP",
        subtitle="Acceso protegido a tu servidor de analisis de YouTube.",
    )


if __name__ == "__main__":
    import sys
    import os

    port = int(os.getenv("PORT", 8000))
    http_mode = "--http" in sys.argv or "PORT" in os.environ

    if http_mode:
        import uvicorn
        uvicorn.run(
            build_http_app(),
            host="0.0.0.0",
            port=port,
            proxy_headers=True,
            forwarded_allow_ips="*",
        )
    else:
        mcp.run()
