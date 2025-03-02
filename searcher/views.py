import requests
import os
from dotenv import load_dotenv

load_dotenv()

def search_song_youtube(song_name):
    api_key = os.getenv("YOUTUBE_API_KEY")  # Твой API-ключ YouTube
    search_url = "https://www.googleapis.com/youtube/v3/search"
    params = {
        "part": "snippet",
        "q": song_name,
        "type": "video",
        "key": api_key,
        "maxResults": 10
    }
    response = requests.get(search_url, params=params)
    if response.status_code == 200:
        data = response.json()
        video_ids = [item["id"]["videoId"] for item in data.get("items", [])]
        return [f"https://www.youtube.com/watch?v={vid}" for vid in video_ids]
    return []

def get_download_link_y2mate(video_url):
    # API Y2Mate (или аналогичный сервис)
    api_url = "https://api.y2mate.com/convert"
    response = requests.post(api_url, json={"url": video_url})
    if response.status_code == 200:
        data = response.json()
        download_url = data.get("download_url", None)  # Получаем ссылку на скачивание
        file_size = data.get("file_size", float('inf'))  # Размер в МБ
        return download_url, file_size
    return None, float('inf')

def search_song(song_name):
    video_links = search_song_youtube(song_name)
    results = []
    
    for link in video_links:
        download_url, file_size = get_download_link_y2mate(link)
        if download_url:
            results.append((download_url, file_size))
    
    results.sort(key=lambda x: x[1])  # Сортируем по размеру файла
    return [link for link, size in results[:10]]  # Возвращаем 10 самых маленьких ссылок
