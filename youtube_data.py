from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import os


def _get_youtube():
    api_key = os.getenv("YOUTUBE_API_KEY")
    if not api_key:
        raise ValueError("YOUTUBE_API_KEY no está configurada en .env")
    return build("youtube", "v3", developerKey=api_key)


def get_channel_stats(channel_id: str) -> dict:
    youtube = _get_youtube()
    try:
        if channel_id.startswith("@"):
            params = {"part": "snippet,statistics", "forHandle": channel_id[1:]}
        else:
            params = {"part": "snippet,statistics", "id": channel_id}

        response = youtube.channels().list(**params).execute()

        if not response.get("items"):
            return {"error": f"Canal no encontrado: {channel_id}"}

        ch = response["items"][0]
        stats = ch["statistics"]
        snippet = ch["snippet"]

        return {
            "channel_id": ch["id"],
            "title": snippet["title"],
            "description": snippet.get("description", "")[:500],
            "country": snippet.get("country", ""),
            "created_at": snippet.get("publishedAt", ""),
            "subscribers": int(stats.get("subscriberCount", 0)),
            "total_views": int(stats.get("viewCount", 0)),
            "video_count": int(stats.get("videoCount", 0)),
            "handle": f"@{snippet.get('customUrl', '').lstrip('@')}",
        }
    except HttpError as e:
        return {"error": str(e)}


def search_youtube(query: str, max_results: int = 10, search_type: str = "video") -> list:
    youtube = _get_youtube()
    try:
        response = youtube.search().list(
            part="snippet",
            q=query,
            type=search_type,
            maxResults=min(max_results, 50),
            relevanceLanguage="es",
        ).execute()

        results = []
        for item in response.get("items", []):
            snippet = item["snippet"]
            result = {
                "title": snippet["title"],
                "channel": snippet["channelTitle"],
                "published_at": snippet["publishedAt"],
                "description": snippet.get("description", "")[:200],
            }
            if search_type == "video":
                vid_id = item["id"].get("videoId", "")
                result["video_id"] = vid_id
                result["url"] = f"https://youtube.com/watch?v={vid_id}"
            elif search_type == "channel":
                result["channel_id"] = item["id"].get("channelId", "")
            results.append(result)

        return results
    except HttpError as e:
        return [{"error": str(e)}]


def get_channel_videos(channel_id: str, max_results: int = 20, order: str = "viewCount") -> list:
    youtube = _get_youtube()
    try:
        ch_response = youtube.channels().list(
            part="contentDetails", id=channel_id
        ).execute()

        if not ch_response.get("items"):
            return [{"error": "Canal no encontrado"}]

        uploads_id = ch_response["items"][0]["contentDetails"]["relatedPlaylists"]["uploads"]

        pl_response = youtube.playlistItems().list(
            part="contentDetails",
            playlistId=uploads_id,
            maxResults=min(max_results, 50),
        ).execute()

        video_ids = [item["contentDetails"]["videoId"] for item in pl_response.get("items", [])]

        if not video_ids:
            return []

        stats_response = youtube.videos().list(
            part="snippet,statistics,contentDetails",
            id=",".join(video_ids),
        ).execute()

        videos = []
        for item in stats_response.get("items", []):
            stats = item.get("statistics", {})
            videos.append({
                "video_id": item["id"],
                "title": item["snippet"]["title"],
                "published_at": item["snippet"]["publishedAt"],
                "views": int(stats.get("viewCount", 0)),
                "likes": int(stats.get("likeCount", 0)),
                "comments": int(stats.get("commentCount", 0)),
                "duration": item["contentDetails"]["duration"],
                "url": f"https://youtube.com/watch?v={item['id']}",
            })

        if order == "viewCount":
            videos.sort(key=lambda x: x["views"], reverse=True)
        else:
            videos.sort(key=lambda x: x["published_at"], reverse=True)

        return videos
    except HttpError as e:
        return [{"error": str(e)}]


def get_video_details(video_id: str) -> dict:
    youtube = _get_youtube()
    try:
        # Acepta URL completa además del ID
        if "youtube.com/watch" in video_id and "v=" in video_id:
            video_id = video_id.split("v=")[1].split("&")[0]
        elif "youtu.be/" in video_id:
            video_id = video_id.split("youtu.be/")[1].split("?")[0]

        response = youtube.videos().list(
            part="snippet,statistics,contentDetails", id=video_id
        ).execute()

        if not response.get("items"):
            return {"error": "Video no encontrado"}

        item = response["items"][0]
        stats = item.get("statistics", {})
        snippet = item["snippet"]

        return {
            "video_id": item["id"],
            "title": snippet["title"],
            "channel": snippet["channelTitle"],
            "channel_id": snippet["channelId"],
            "published_at": snippet["publishedAt"],
            "tags": snippet.get("tags", []),
            "duration": item["contentDetails"]["duration"],
            "views": int(stats.get("viewCount", 0)),
            "likes": int(stats.get("likeCount", 0)),
            "comments": int(stats.get("commentCount", 0)),
            "url": f"https://youtube.com/watch?v={item['id']}",
            "description": snippet.get("description", "")[:1000],
        }
    except HttpError as e:
        return {"error": str(e)}
