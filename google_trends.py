from pytrends.request import TrendReq


def _pytrends():
    return TrendReq(hl="es-419", tz=360, timeout=(10, 25), retries=2, backoff_factor=0.5)


def keyword_trends(keywords: list, country: str = "MX", timeframe: str = "today 3-m") -> list:
    try:
        pt = _pytrends()
        pt.build_payload(keywords, cat=0, timeframe=timeframe, geo=country)
        data = pt.interest_over_time()

        if data.empty:
            return []

        data = data.drop(columns=["isPartial"], errors="ignore")
        # Convertir timestamps a string para que sea serializable en JSON
        data.index = data.index.astype(str)
        return data.reset_index().rename(columns={"index": "date"}).to_dict("records")
    except Exception as e:
        return [{"error": str(e)}]


def trending_now(country: str = "MX") -> list:
    """
    Usa YouTube Data API para obtener los videos en tendencia.
    Se importa aquí para evitar dependencia circular.
    """
    try:
        from youtube_data import _get_youtube
        youtube = _get_youtube()
        response = youtube.videos().list(
            part="snippet,statistics",
            chart="mostPopular",
            regionCode=country.upper(),
            maxResults=25,
        ).execute()

        results = []
        for item in response.get("items", []):
            snippet = item["snippet"]
            stats = item.get("statistics", {})
            results.append({
                "title": snippet["title"],
                "channel": snippet["channelTitle"],
                "views": int(stats.get("viewCount", 0)),
                "video_id": item["id"],
                "url": f"https://youtube.com/watch?v={item['id']}",
            })
        return results
    except Exception as e:
        return [{"error": str(e)}]


def related_keywords(keyword: str, country: str = "MX") -> dict:
    try:
        pt = _pytrends()
        pt.build_payload([keyword], geo=country, timeframe="today 3-m")
        related = pt.related_queries()

        result = {"top": [], "rising": []}
        if keyword in related:
            if related[keyword]["top"] is not None:
                result["top"] = related[keyword]["top"].to_dict("records")
            if related[keyword]["rising"] is not None:
                result["rising"] = related[keyword]["rising"].to_dict("records")

        return result
    except Exception as e:
        return {"error": str(e)}


def keyword_by_region(keyword: str, country: str = "MX") -> list:
    try:
        pt = _pytrends()
        pt.build_payload([keyword], geo=country, timeframe="today 3-m")
        data = pt.interest_by_region(resolution="REGION", inc_geo_code=True)

        if data.empty:
            return []

        data = data.sort_values(keyword, ascending=False)
        return data.reset_index().to_dict("records")
    except Exception as e:
        return [{"error": str(e)}]
