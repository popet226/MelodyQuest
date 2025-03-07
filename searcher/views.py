import requests
import os
from dotenv import load_dotenv
import yt_dlp

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


def get_download_link_yt_dlp(video_url):
    ydl_opts = {
        'format': 'bestaudio/best',
        'quiet': True,
        'noplaylist': True,
        'extractaudio': True,
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
    }
    
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        try:
            info = ydl.extract_info(video_url, download=False)
            download_url = info.get('url')
            file_size = info.get('filesize', float('inf'))
            
            if not download_url:
                print("Ошибка: ссылка на скачивание не найдена.")
                return None, None
            
            return download_url, file_size
        except Exception as e:
            print(f"Ошибка при получении ссылки: {e}")
            return None, None


def search_song(song_name):
    video_links = search_song_youtube(song_name)
    results = []
    
    for link in video_links:
        download_url, file_size = get_download_link_yt_dlp(link)
        if download_url:
            results.append((download_url, file_size))
    
    results.sort(key=lambda x: x[1])  # Сортируем по размеру файла
    return [link for link, size in results[:10]]  # Возвращаем 10 самых маленьких ссылок
