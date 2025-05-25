import requests
import os
from dotenv import load_dotenv
import yt_dlp
import logging
import time
from bs4 import BeautifulSoup
import json
from urllib.parse import quote

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

COMMON_HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36',
    'Accept': 'audio/mp4,audio/webm,*/*;q=0.9',
}

def write_cookies_from_env(env_var_name='YOUTUBE_COOKIES', filepath='cookies.txt'):
    cookies_content = os.getenv(env_var_name)
    if not cookies_content:
        raise RuntimeError(f"Переменная окружения {env_var_name} не задана!")
    

    if os.path.exists(filepath):
        try:
            os.remove(filepath)
            print(f"Удалён старый файл куков: {filepath}")
        except Exception as e:
            raise RuntimeError(f"Не удалось удалить старый файл: {e}")
    
    cookies_text = cookies_content.encode('utf-8').decode('unicode_escape')
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(cookies_text)
    print(f"Файл с куками записан: {filepath}")

def get_file_size(url):
    """Получает размер файла по URL без скачивания всего файла"""
    try:
        response = requests.head(url, headers=COMMON_HEADERS, allow_redirects=True, timeout=5)
        if response.status_code == 200:
            size = int(response.headers.get('content-length', 0))
            return size if size > 0 else None
    except Exception as e:
        logger.error(f"Ошибка при получении размера файла: {e}")
    return None

def search_song_hitmotop(song_name):
    results = []
    try:
        encoded_query = quote(song_name)
        response = requests.get(
            f'https://rus.hitmotop.com/search?q={encoded_query}',
            headers=COMMON_HEADERS,
            timeout=10
        )
        
        if response.status_code != 200:
            logger.error(f"Hitmotop: Ошибка запроса - {response.status_code}")
            return results
            
        soup = BeautifulSoup(response.text, 'html.parser')
        track_items = soup.find_all('li', class_='tracks__item track mustoggler')

        if not track_items:
            logger.info("Hitmotop: Треки не найдены")
            return results

        for item in track_items[:5]: 
            musmeta = item.get('data-musmeta')
            if not musmeta:
                continue
                
            try:
                musmeta_data = json.loads(musmeta.replace('&quot;', '"'))
                download_url = musmeta_data.get('url')
                if not download_url:
                    continue
                    
                file_size = get_file_size(download_url)
                
                results.append((download_url, file_size))
                
            except Exception as e:
                logger.error(f"Hitmotop: Ошибка обработки данных трека: {e}")

    except Exception as e:
        logger.error(f"Hitmotop: Ошибка при поиске: {e}")
        
    return results

def search_song_youtube(song_name):

    api_key = os.getenv("YOUTUBE_API_KEY")
    if not api_key:
        logger.error("YouTube API ключ не найден")
        return []
        
    search_url = "https://www.googleapis.com/youtube/v3/search"
    params = {
        "part": "snippet",
        "q": song_name,
        "type": "video",
        "key": api_key,
        "maxResults": 5
    }
    
    try:
        response = requests.get(search_url, params=params, timeout=10)
        if response.status_code == 200:
            data = response.json()
            video_ids = [item["id"]["videoId"] for item in data.get("items", [])]
            return [f"https://www.youtube.com/watch?v={vid}" for vid in video_ids]
        else:
            logger.error(f"YouTube API: Ошибка {response.status_code} - {response.text}")
    except Exception as e:
        logger.error(f"YouTube: Ошибка при поиске: {e}")
        
    return []

def get_download_link_yt_dlp(video_url):
    ydl_opts = {
        'format': 'bestaudio[ext=m4a]/bestaudio[ext=webm]/bestaudio[acodec=aac]/bestaudio[acodec=opus][ext=webm][protocol!=hls][protocol!=m3u8]',
        'quiet': True,
        'noplaylist': True,
        'extractaudio': True,
        'geturl': True,
        'http_headers': COMMON_HEADERS, 
        'cookiefile': r'D:\University\SecondTry\music_searcher\searcher\cookies.txt',
    }
    
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        try:
            info = ydl.extract_info(video_url, download=False)
            download_url = info.get('url') or info.get('direct_link')
            file_size = info.get('filesize', float('inf'))
            format_ext = info.get('ext', 'unknown')
            protocol = info.get('protocol', 'unknown')
            
            if not download_url:
                logger.error("YouTube: Ссылка на скачивание не найдена")
                return None, None
                
            if protocol in ('hls', 'm3u8'):
                logger.error(f"YouTube: Потоковый формат (protocol={protocol}, ext={format_ext})")
                return None, None
                
            logger.info(f"YouTube: Получена ссылка (Формат: {format_ext}, Размер: {file_size})")
            return download_url, file_size
            
        except Exception as e:
            logger.error(f"YouTube: Ошибка при получении ссылки: {e}")
            return None, None

def search_song(song_name):
    if not song_name or not song_name.strip():
        return []
    
    write_cookies_from_env(filepath='D:/University/SecondTry/music_searcher/searcher/cookies.txt')
        
    song_name = song_name.strip()
    logger.info(f"Начало поиска для: '{song_name}'")
    
    hitmotop_results = search_song_hitmotop(song_name)
    
    youtube_results = []
    video_links = search_song_youtube(song_name)
    for link in video_links:
        download_url, file_size = get_download_link_yt_dlp(link)
        if download_url:
            youtube_results.append((download_url, file_size))
        time.sleep(0.5)
    
    combined_results = hitmotop_results[:2] + youtube_results[:3]
    

    logger.info(f"Найдено результатов: {len(combined_results)}")
    for idx, (url, size) in enumerate(combined_results, 1):
        size_str = f"{size/1024/1024:.1f} MB" if size and size != float('inf') else "unknown"
        logger.info(f"Результат {idx}: {url[:60]}... (размер: {size_str})")
    
    return combined_results[:5] 