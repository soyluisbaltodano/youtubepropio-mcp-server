from mcp.server.fastmcp import FastMCP
from dotenv import load_dotenv
from pathlib import Path
import json

# Carga el .env desde la carpeta del servidor, sin importar desde dónde se ejecute
load_dotenv(Path(__file__).parent / ".env")

from youtube_data import get_channel_stats, search_youtube, get_channel_videos, get_video_details
from youtube_analytics import get_my_analytics, get_traffic_sources, get_top_videos_analytics
from google_trends import keyword_trends, trending_now, related_keywords, keyword_by_region

mcp = FastMCP("youtube-mcp")


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


if __name__ == "__main__":
    import sys
    import os

    # En Render (nube) el PORT viene como variable de entorno
    port = int(os.getenv("PORT", 8000))
    http_mode = "--http" in sys.argv or "PORT" in os.environ

    if http_mode:
        mcp.run(transport="sse", host="0.0.0.0", port=port)
    else:
        mcp.run()
