import os
import re
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError


def _get_youtube():
    api_key = os.getenv("YOUTUBE_API_KEY")
    if not api_key:
        raise ValueError("YOUTUBE_API_KEY no está configurada en .env")
    return build("youtube", "v3", developerKey=api_key)


def _extract_video_id(video_id_or_url: str) -> str:
    match = re.search(r'(?:v=|/v/|youtu\.be/|/embed/)([a-zA-Z0-9_-]{11})', video_id_or_url)
    return match.group(1) if match else video_id_or_url


def _resolve_channel_id(channel_id: str) -> str:
    """Convierte @handle a channel ID si es necesario."""
    if not channel_id.startswith("@"):
        return channel_id
    yt = _get_youtube()
    resp = yt.channels().list(part="id", forHandle=channel_id[1:]).execute()
    items = resp.get("items", [])
    if not items:
        raise ValueError(f"No se encontró el canal: {channel_id}")
    return items[0]["id"]


def get_video_transcript(video_id: str, language: str = "es") -> dict:
    """Obtiene la transcripción/subtítulos de un video de YouTube."""
    from youtube_transcript_api import YouTubeTranscriptApi
    from youtube_transcript_api._errors import TranscriptsDisabled, NoTranscriptFound

    vid_id = _extract_video_id(video_id)
    api = YouTubeTranscriptApi()

    try:
        # Intentar idioma preferido, luego inglés, luego cualquiera disponible
        transcript_ref = None
        transcript_list = api.list(vid_id)

        for lang in [language, "en"]:
            try:
                transcript_ref = transcript_list.find_transcript([lang])
                break
            except NoTranscriptFound:
                continue

        if transcript_ref is None:
            all_transcripts = list(transcript_list)
            if not all_transcripts:
                return {"error": "No hay transcripciones disponibles para este video"}
            transcript_ref = all_transcripts[0]

        data = transcript_ref.fetch()
        full_text = " ".join([segment.text for segment in data])

        return {
            "video_id": vid_id,
            "language": transcript_ref.language_code,
            "language_name": transcript_ref.language,
            "is_auto_generated": transcript_ref.is_generated,
            "word_count": len(full_text.split()),
            "segment_count": len(data),
            "transcript": full_text,
        }
    except TranscriptsDisabled:
        return {"error": "Este video tiene los subtítulos desactivados"}
    except Exception as e:
        return {"error": str(e)}


def get_channel_rss(channel_id: str, max_results: int = 15) -> dict:
    """Obtiene los últimos videos de un canal via RSS (sin consumir quota de API)."""
    import feedparser

    resolved_id = _resolve_channel_id(channel_id)
    rss_url = f"https://www.youtube.com/feeds/videos.xml?channel_id={resolved_id}"
    feed = feedparser.parse(rss_url)

    if not feed.entries:
        return {"error": "No se pudo obtener el feed RSS", "channel_id": resolved_id}

    videos = []
    for entry in feed.entries[:max_results]:
        desc = entry.get("summary", "")
        video = {
            "title": entry.get("title", ""),
            "video_id": entry.get("yt_videoid", ""),
            "url": entry.get("link", ""),
            "published": entry.get("published", ""),
            "description": desc[:200] + "..." if len(desc) > 200 else desc,
        }
        # Vistas disponibles en media:statistics
        media_stats = entry.get("media_statistics", {})
        if media_stats:
            video["views"] = int(media_stats.get("views", 0))
        videos.append(video)

    return {
        "channel_name": feed.feed.get("title", ""),
        "channel_id": resolved_id,
        "videos_returned": len(videos),
        "source": "RSS (sin quota API)",
        "videos": videos,
    }


def get_video_comments(video_id: str, max_results: int = 20, order: str = "relevance") -> dict:
    """Obtiene los comentarios top de un video. order: 'relevance' o 'time'."""
    vid_id = _extract_video_id(video_id)
    yt = _get_youtube()

    try:
        resp = yt.commentThreads().list(
            part="snippet",
            videoId=vid_id,
            maxResults=min(max_results, 100),
            order=order,
            textFormat="plainText",
        ).execute()

        comments = []
        for item in resp.get("items", []):
            top = item["snippet"]["topLevelComment"]["snippet"]
            comments.append({
                "author": top.get("authorDisplayName", ""),
                "text": top.get("textDisplay", ""),
                "likes": top.get("likeCount", 0),
                "published_at": top.get("publishedAt", ""),
                "reply_count": item["snippet"].get("totalReplyCount", 0),
            })

        return {
            "video_id": vid_id,
            "order": order,
            "comments_returned": len(comments),
            "comments": comments,
        }
    except HttpError as e:
        error_str = str(e)
        if "commentsDisabled" in error_str:
            return {"error": "Los comentarios están desactivados en este video"}
        return {"error": error_str}


def compare_channels(channel_ids: list) -> dict:
    """Compara stats de 2-4 canales. Acepta @handles o channel IDs."""
    from youtube_data import get_channel_stats

    results = []
    for cid in channel_ids[:4]:
        stats = get_channel_stats(cid)
        if "error" in stats:
            results.append({"handle": cid, "error": stats["error"]})
        else:
            video_count = max(stats.get("video_count", 1), 1)
            results.append({
                "handle": stats.get("handle", cid),
                "name": stats.get("title", ""),
                "country": stats.get("country", "N/A"),
                "subscribers": stats.get("subscribers", 0),
                "total_views": stats.get("total_views", 0),
                "video_count": stats.get("video_count", 0),
                "avg_views_per_video": int(stats.get("total_views", 0) / video_count),
                "channel_id": stats.get("channel_id", ""),
            })

    valid = [r for r in results if "error" not in r]
    valid.sort(key=lambda x: x.get("subscribers", 0), reverse=True)
    errors = [r for r in results if "error" in r]

    for i, ch in enumerate(valid, 1):
        ch["rank"] = i

    return {
        "channels_compared": len(results),
        "ranking": valid + errors,
    }


def get_channel_playlists(channel_id: str, max_results: int = 20) -> dict:
    """Lista las playlists de un canal con cantidad de videos."""
    resolved_id = _resolve_channel_id(channel_id)
    yt = _get_youtube()

    try:
        resp = yt.playlists().list(
            part="snippet,contentDetails",
            channelId=resolved_id,
            maxResults=min(max_results, 50),
        ).execute()

        playlists = []
        for item in resp.get("items", []):
            snippet = item.get("snippet", {})
            desc = snippet.get("description", "")
            playlists.append({
                "id": item["id"],
                "title": snippet.get("title", ""),
                "description": desc[:150] + "..." if len(desc) > 150 else desc,
                "published_at": snippet.get("publishedAt", ""),
                "video_count": item.get("contentDetails", {}).get("itemCount", 0),
                "url": f"https://www.youtube.com/playlist?list={item['id']}",
                "thumbnail": snippet.get("thumbnails", {}).get("medium", {}).get("url", ""),
            })

        playlists.sort(key=lambda x: x["video_count"], reverse=True)

        return {
            "channel_id": resolved_id,
            "playlists_returned": len(playlists),
            "playlists": playlists,
        }
    except HttpError as e:
        return {"error": str(e)}
