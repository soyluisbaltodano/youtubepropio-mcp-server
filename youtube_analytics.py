from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
import os

SCOPES = [
    "https://www.googleapis.com/auth/youtube.readonly",
    "https://www.googleapis.com/auth/yt-analytics.readonly",
]

# En Render, Secret Files van a /etc/secrets/<filename>
TOKEN_PATH = (
    "/etc/secrets/token.json"
    if os.path.exists("/etc/secrets/token.json")
    else os.path.join(os.path.dirname(__file__), "credentials", "token.json")
)
CREDENTIALS_PATH = os.getenv(
    "OAUTH_CREDENTIALS_PATH",
    os.path.join(os.path.dirname(__file__), "credentials", "oauth_client.json"),
)

TRAFFIC_LABELS = {
    "YT_SEARCH": "Búsqueda de YouTube",
    "SUGGESTED_VIDEOS": "Videos sugeridos",
    "EXTERNAL": "Fuentes externas",
    "CHANNEL": "Página del canal",
    "BROWSE_FEATURES": "Inicio / Explorar",
    "PLAYLIST": "Listas de reproducción",
    "NOTIFICATION": "Notificaciones",
    "NO_LINK_OTHER": "Otros",
    "END_SCREEN": "Pantalla final",
    "SHORTS": "YouTube Shorts",
}


def _get_credentials() -> Credentials:
    creds = None

    if os.path.exists(TOKEN_PATH):
        creds = Credentials.from_authorized_user_file(TOKEN_PATH, SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_PATH, SCOPES)
            # Abre el navegador para autorizar — solo ocurre la primera vez
            creds = flow.run_local_server(port=0)

        os.makedirs(os.path.dirname(TOKEN_PATH), exist_ok=True)
        with open(TOKEN_PATH, "w") as f:
            f.write(creds.to_json())

    return creds


def _get_my_channel_id(creds: Credentials) -> str | None:
    youtube = build("youtube", "v3", credentials=creds)
    response = youtube.channels().list(part="id", mine=True).execute()
    if response.get("items"):
        return response["items"][0]["id"]
    return None


def get_my_analytics(start_date: str, end_date: str, metrics: str, dimensions: str) -> dict:
    try:
        creds = _get_credentials()
        channel_id = _get_my_channel_id(creds)
        if not channel_id:
            return {"error": "No se pudo obtener el canal autorizado"}

        service = build("youtubeAnalytics", "v2", credentials=creds)
        response = service.reports().query(
            ids=f"channel=={channel_id}",
            startDate=start_date,
            endDate=end_date,
            metrics=metrics,
            dimensions=dimensions,
        ).execute()

        headers = [col["name"] for col in response.get("columnHeaders", [])]
        rows = response.get("rows", [])

        return {
            "period": {"start": start_date, "end": end_date},
            "headers": headers,
            "data": [dict(zip(headers, row)) for row in rows],
        }
    except Exception as e:
        return {"error": str(e)}


def get_traffic_sources(start_date: str, end_date: str) -> dict:
    try:
        creds = _get_credentials()
        channel_id = _get_my_channel_id(creds)
        service = build("youtubeAnalytics", "v2", credentials=creds)

        response = service.reports().query(
            ids=f"channel=={channel_id}",
            startDate=start_date,
            endDate=end_date,
            metrics="views,estimatedMinutesWatched",
            dimensions="insightTrafficSourceType",
            sort="-views",
        ).execute()

        headers = [col["name"] for col in response.get("columnHeaders", [])]
        rows = response.get("rows", [])

        data = []
        for row in rows:
            entry = dict(zip(headers, row))
            source = entry.get("insightTrafficSourceType", "")
            entry["source_label"] = TRAFFIC_LABELS.get(source, source)
            data.append(entry)

        return {"period": {"start": start_date, "end": end_date}, "traffic_sources": data}
    except Exception as e:
        return {"error": str(e)}


def get_top_videos_analytics(start_date: str, end_date: str, limit: int = 10) -> dict:
    try:
        creds = _get_credentials()
        channel_id = _get_my_channel_id(creds)
        service = build("youtubeAnalytics", "v2", credentials=creds)

        response = service.reports().query(
            ids=f"channel=={channel_id}",
            startDate=start_date,
            endDate=end_date,
            metrics="views,estimatedMinutesWatched,averageViewPercentage,likes,comments,subscribersGained",
            dimensions="video",
            sort="-views",
            maxResults=limit,
        ).execute()

        headers = [col["name"] for col in response.get("columnHeaders", [])]
        rows = response.get("rows", [])

        return {
            "period": {"start": start_date, "end": end_date},
            "top_videos": [dict(zip(headers, row)) for row in rows],
        }
    except Exception as e:
        return {"error": str(e)}
