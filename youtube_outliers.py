import os
import statistics
from datetime import datetime, timedelta, timezone
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError


def _get_youtube():
    api_key = os.getenv("YOUTUBE_API_KEY")
    if not api_key:
        raise ValueError("YOUTUBE_API_KEY no está configurada en .env")
    return build("youtube", "v3", developerKey=api_key)


def _channel_baseline(yt, channel_id: str, exclude_video_id: str = None, sample_size: int = 15) -> dict:
    """Mediana de vistas de los últimos videos del canal — la 'normalidad' contra la que se mide el outlier."""
    ch_resp = yt.channels().list(part="contentDetails,statistics", id=channel_id).execute()
    items = ch_resp.get("items", [])
    if not items:
        return {"median_views": None, "subscribers": 0}

    uploads_id = items[0]["contentDetails"]["relatedPlaylists"]["uploads"]
    subscribers = int(items[0]["statistics"].get("subscriberCount", 0))

    pl_resp = yt.playlistItems().list(
        part="contentDetails", playlistId=uploads_id, maxResults=min(sample_size + 1, 50)
    ).execute()
    video_ids = [it["contentDetails"]["videoId"] for it in pl_resp.get("items", [])]
    video_ids = [v for v in video_ids if v != exclude_video_id][:sample_size]

    if not video_ids:
        return {"median_views": None, "subscribers": subscribers}

    stats_resp = yt.videos().list(part="statistics", id=",".join(video_ids)).execute()
    views = [int(it["statistics"].get("viewCount", 0)) for it in stats_resp.get("items", [])]
    if not views:
        return {"median_views": None, "subscribers": subscribers}

    return {"median_views": statistics.median(views), "subscribers": subscribers, "sample_size": len(views)}


def find_outliers(
    niche: str,
    max_candidates: int = 25,
    min_score: float = 3.0,
    max_results: int = 15,
    published_after_days: int = None,
) -> dict:
    """
    Busca videos "outlier" para un nicho/tema: videos que superan por mucho el promedio normal
    de su propio canal. outlier_score = vistas del video / mediana de vistas de los últimos
    videos del canal (excluyendo el video candidato).
    """
    yt = _get_youtube()

    search_params = {
        "part": "snippet",
        "q": niche,
        "type": "video",
        "maxResults": min(max_candidates, 50),
        "relevanceLanguage": "es",
        "order": "relevance",
    }
    if published_after_days:
        after = datetime.now(timezone.utc) - timedelta(days=published_after_days)
        search_params["publishedAfter"] = after.isoformat().replace("+00:00", "Z")

    try:
        search_resp = yt.search().list(**search_params).execute()
    except HttpError as e:
        return {"error": str(e)}

    video_ids = [it["id"]["videoId"] for it in search_resp.get("items", []) if it["id"].get("videoId")]
    if not video_ids:
        return {"niche": niche, "candidates_checked": 0, "outliers_found": 0, "results": []}

    try:
        videos_resp = yt.videos().list(part="snippet,statistics", id=",".join(video_ids)).execute()
    except HttpError as e:
        return {"error": str(e)}

    baseline_cache = {}
    results = []

    for item in videos_resp.get("items", []):
        vid_id = item["id"]
        snippet = item["snippet"]
        channel_id = snippet["channelId"]
        views = int(item.get("statistics", {}).get("viewCount", 0))

        if channel_id not in baseline_cache:
            try:
                baseline_cache[channel_id] = _channel_baseline(yt, channel_id, exclude_video_id=vid_id)
            except HttpError as e:
                baseline_cache[channel_id] = {"median_views": None, "subscribers": 0, "error": str(e)}
        baseline = baseline_cache[channel_id]

        median_views = baseline.get("median_views")
        if not median_views:
            continue

        score = round(views / median_views, 2)
        if score < min_score:
            continue

        results.append({
            "video_id": vid_id,
            "title": snippet["title"],
            "channel": snippet["channelTitle"],
            "channel_id": channel_id,
            "channel_subscribers": baseline.get("subscribers", 0),
            "published_at": snippet["publishedAt"],
            "views": views,
            "channel_median_views": int(median_views),
            "outlier_score": score,
            "url": f"https://youtube.com/watch?v={vid_id}",
            "thumbnail": snippet.get("thumbnails", {}).get("medium", {}).get("url", ""),
        })

    results.sort(key=lambda x: x["outlier_score"], reverse=True)

    return {
        "niche": niche,
        "candidates_checked": len(video_ids),
        "outliers_found": len(results),
        "min_score_filter": min_score,
        "results": results[:max_results],
    }
