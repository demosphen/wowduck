from flask import Flask, render_template, request
from flask_caching import Cache
import requests
import os

app = Flask(__name__)

# Настройки кеширования
cache = Cache(app, config={'CACHE_TYPE': 'simple'})

# Константы
API_KEY = "AIzaSyCc8r2oe7PBXrjVB-SkMTWlMcgXlXWFZNc"
MAX_RESULTS = 5  # Изменил на число, так как это количество видео

def fetch_data(url):
    """Выполняет запрос к API и возвращает JSON-данные."""
    try:
        response = requests.get(url)
        response.raise_for_status()  # Проверка на ошибки HTTP
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Ошибка при выполнении запроса: {e}")
        return None

def calculate_percentage(value, total):
    """Вычисляет процентное значение."""
    return (value / total) * 100 if total != 0 else 0

def get_cache_key_search_channel(channel_name):
    return f'search_channel_{channel_name}'

def get_cache_key_channel_data(channel_id):
    return f'channel_data_{channel_id}'

@app.route('/', methods=['GET', 'POST'])
def index():
    stats = None
    error = None

    if request.method == 'POST':
        channel_name = request.form.get('channel_name')

        if not channel_name:
            error = "Пожалуйста, введите название канала."
        else:
            search_cache_key = get_cache_key_search_channel(channel_name)
            search_data = cache.get(search_cache_key)

            if not search_data:
                search_url = f"https://www.googleapis.com/youtube/v3/search?part=snippet&type=channel&q={channel_name}&key={API_KEY}"
                search_data = fetch_data(search_url)
                cache.set(search_cache_key, search_data, timeout=3600)

            if not search_data or "items" not in search_data or not search_data["items"]:
                error = "Канал с таким названием не найден."
            else:
                channel_id = search_data["items"][0]["snippet"]["channelId"]

                channel_cache_key = get_cache_key_channel_data(channel_id)
                channel_data = cache.get(channel_cache_key)

                if not channel_data:
                    channel_url = f"https://www.googleapis.com/youtube/v3/channels?part=snippet,statistics&id={channel_id}&key={API_KEY}"
                    channel_data = fetch_data(channel_url)
                    cache.set(channel_cache_key, channel_data, timeout=3600)

                videos_data = fetch_data(
                    f"https://www.googleapis.com/youtube/v3/search?part=snippet&channelId={channel_id}&order=date&maxResults={MAX_RESULTS}&key={API_KEY}"
                )

                if not channel_data or "items" not in channel_data or not channel_data["items"]:
                    error = "Ошибка: не удалось получить данные о канале."
                elif not videos_data or "items" not in videos_data or not videos_data["items"]:
                    error = "Ошибка: не удалось получить данные о видео."
                else:
                    video_ids = [video["id"].get("videoId", None) for video in videos_data["items"]]
                    video_ids = list(filter(None, video_ids))  # Исключение None из списка

                    if not video_ids:
                        error = "Ошибка: не удалось получить ID видео."
                    else:
                        stats_data = fetch_data(
                            f"https://www.googleapis.com/youtube/v3/videos?part=statistics&id={','.join(video_ids)}&key={API_KEY}"
                        )

                        if not stats_data or "items" not in stats_data or not stats_data["items"]:
                            error = "Ошибка: не удалось получить статистику по видео."
                        else:
                            total_views = sum(int(video["statistics"].get("viewCount", 0)) for video in stats_data["items"])
                            total_likes = sum(int(video["statistics"].get("likeCount", 0)) for video in stats_data["items"])
                            total_comments = sum(int(video["statistics"].get("commentCount", 0)) for video in stats_data["items"])

                            num_videos = len(video_ids)
                            avg_views = total_views / num_videos
                            avg_likes = total_likes / num_videos
                            avg_comments = total_comments / num_videos

                            subscriber_count = int(channel_data["items"][0]["statistics"]["subscriberCount"])

                            view_percentage = calculate_percentage(avg_views, subscriber_count)
                            like_percentage = calculate_percentage(avg_likes, subscriber_count)
                            comment_percentage = calculate_percentage(avg_comments, subscriber_count)

                            stats = {
                                "channel_name": channel_data["items"][0]["snippet"]["title"],
                                "avg_views": round(avg_views, 2),
                                "avg_likes": round(avg_likes, 2),
                                "avg_comments": round(avg_comments, 2),
                                "subscriber_count": subscriber_count,
                                "view_percentage": round(view_percentage, 2),
                                "like_percentage": round(like_percentage, 2),
                                "comment_percentage": round(comment_percentage, 2),
                                "total_likes_comments": round((total_likes + total_comments) / num_videos / subscriber_count * 100, 2),
                            }

    return render_template('index.html', stats=stats, error=error)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
