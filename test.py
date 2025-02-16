import requests

# API-ключ
API_KEY = "AIzaSyCc8r2oe7PBXrjVB-SkMTWlMcgXlXWFZNc"

# Идентификатор канала
CHANNEL_ID = "UCvOdcNsj4xrmvFJDCgM5obQ"

# URL для запроса данных о канале
url = f"https://www.googleapis.com/youtube/v3/channels?part=statistics&id={CHANNEL_ID}&key={API_KEY}"
url_videos = f"https://www.googleapis.com/youtube/v3/search?part=snippet&channelId={CHANNEL_ID}&order=date&maxResults=5&key={API_KEY}"

try:
    # Запрос данных о последних 5 видео
    response_videos = requests.get(url_videos)
    response_videos.raise_for_status()  # Проверка на ошибки HTTP
    videos_data = response_videos.json()

    if "items" in videos_data and videos_data["items"]:
        video_ids = [video["id"]["videoId"] for video in videos_data["items"]]

        # Запрос статистики по видео
        url_video_stats = f"https://www.googleapis.com/youtube/v3/videos?part=statistics&id={','.join(video_ids)}&key={API_KEY}"
        response_stats = requests.get(url_video_stats)
        response_stats.raise_for_status()
        stats_data = response_stats.json()

        total_views = 0
        total_likes = 0
        total_comments = 0

        # Суммируем показатели по последним 5 видео
        for video in stats_data["items"]:
            total_views += int(video["statistics"].get("viewCount", 0))
            total_likes += int(video["statistics"].get("likeCount", 0))
            total_comments += int(video["statistics"].get("commentCount", 0))
       # print(total_comments,total_likes,total_views)
        # Средние значения
        avg_views = total_views / len(video_ids)
        avg_likes = total_likes / len(video_ids)
        avg_comments = total_comments / len(video_ids)

        print(f"Среднее количество просмотров за последние 5 видео: {avg_views}")
        print(f"Среднее количество лайков за последние 5 видео: {avg_likes}")
        print(f"Среднее количество комментариев за последние 5 видео: {avg_comments}")

        # Запрос данных о подписчиках
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()

        if "items" in data and data["items"]:
            subscriber_count = int(data["items"][0]["statistics"]["subscriberCount"])

            view_percentage = (avg_views / subscriber_count) * 100

            like_percentage = (avg_likes / subscriber_count) * 100
            comment_percentage = (total_comments / subscriber_count) * 100

            print(f"Процент просмотров от количества подписчиков: {view_percentage:.2f}%")
            print(f"Процент лайков от количества подписчиков: {like_percentage:.2f}%")
            print(f"Процент комментариев от количества подписчиков: {comment_percentage:.2f}%")
            print(f"Среднее количество комментариев и лайков от количества подписчиков: {total_comments+total_likes:}")
            print(f"Количество подписчиков: {subscriber_count}")

        else:
            print("Ошибка: не удалось получить данные о канале.")
    else:
        print("Ошибка: не удалось получить данные о видео.")
except requests.exceptions.RequestException as e:
    print(f"Ошибка при выполнении запроса: {e}")