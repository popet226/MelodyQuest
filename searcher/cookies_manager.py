import browser_cookie3
import tempfile
import os

def get_youtube_cookies():
    """Ищет куки YouTube в любом из браузеров."""
    browsers = [
        browser_cookie3.chrome,
        browser_cookie3.firefox,
        browser_cookie3.edge,
        browser_cookie3.opera,
        browser_cookie3.brave,
    ]

    for browser in browsers:
        try:
            cj = browser(domain_name='youtube.com')
            if cj and len(cj) > 0:
                return cj
        except Exception:
            continue

    raise RuntimeError("Не удалось найти куки YouTube ни в одном из браузеров.")

def write_cookies_to_tempfile():
    """Записывает куки YouTube во временный файл и возвращает путь к нему."""
    cj = get_youtube_cookies()

    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".txt", mode='w', encoding='utf-8')
    tmp.write("# Netscape HTTP Cookie File\n")
    for cookie in cj:
        tmp.write("\t".join([
            cookie.domain,
            "TRUE" if cookie.domain.startswith('.') else "FALSE",
            cookie.path,
            "TRUE" if cookie.secure else "FALSE",
            str(cookie.expires or 0),
            cookie.name,
            cookie.value
        ]) + "\n")
    tmp.close()
    return tmp.name

def remove_temp_cookie_file(filepath):
    """Удаляет временный файл с куками."""
    try:
        if filepath and os.path.exists(filepath):
            os.remove(filepath)
    except Exception as e:
        print(f"Ошибка при удалении временного файла куков: {e}")
