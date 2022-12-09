import re
from httpx import AsyncClient
from pytube import YouTube

from root.settings import API_KEY


def humanbytes(size):
    # https://stackoverflow.com/a/49361727/4723940
    # 2**10 = 1024
    if not size:
        return ""
    power = 2 ** 10
    n = 0
    Dic_powerN = {0: ' ', 1: 'Ki', 2: 'Mi', 3: 'Gi', 4: 'Ti'}
    while size > power:
        size /= power
        n += 1
    return str(round(size, 2)) + " " + Dic_powerN[n] + 'B'


def video_id(url):
    regex = re.compile(r'((?<=(v|V)/)|(?<=be/)|(?<=(\?|\&)v=)|(?<=embed/))([\w-]+)')
    matches = re.search(regex, url)

    return matches.group(matches.lastindex)


async def get_channel_data(channel_id):
    try:
        async with AsyncClient() as client:
            url = 'https://www.googleapis.com/youtube/v3/channels'
            data = {'part': 'statistics,brandingSettings', 'id': channel_id, 'key': API_KEY}
            r = await client.get(url, params=data)
            if r.status_code != 200:
                return False
            statistics = r.json()['items'][0]['statistics']
            branding = r.json()['items'][0]['brandingSettings']
        return {
            'title': branding['channel'].get('title'),
            'description': branding['channel'].get('description'),
            'keywords': branding['channel'].get('keywords'),
            'country': branding['channel'].get('country'),
            'bannerExternalUrl': branding['image'].get('bannerExternalUrl'),
            'unsubscribedTrailer': 'https://www.youtube.com/watch?v=' + branding['channel'].get(
                'unsubscribedTrailer') if branding['channel'].get('unsubscribedTrailer') else 'None',
            'id': channel_id,
            'url': 'https://www.youtube.com/channel/' + channel_id,
            'videoCount': statistics.get('videoCount'),
            'viewCount': statistics.get('viewCount'),
            'subscriberCount': statistics.get('subscriberCount'),
            'hiddenSubscriberCount': statistics.get('hiddenSubscriberCount')
        }
    except KeyError:
        return False


async def get_video_data(video_url):
    try:
        async with AsyncClient() as client:
            url = 'https://www.googleapis.com/youtube/v3/videos?part=snippet,contentDetails,statistics'
            data = {'id': video_id(video_url), 'key': API_KEY}
            r = await client.get(url, params=data)
            yt = YouTube(video_url)
            stream = yt.streams.filter()
            if r.status_code != 200:
                return False

            video = r.json()['items'][0]
            downloads = {'video': [], 'audio': []}
            for item in stream:
                dl = {
                    'type': item.subtype,
                    'quality': item.resolution,
                    'filesize': humanbytes(item.filesize),
                    'url': item.url,
                    'format': item.subtype
                }
                if item.type == 'video':
                    downloads['video'].append(dl)
                else:
                    dl['quality'] = item.abr
                    downloads['audio'].append(dl)
        return {
            'title': video['snippet'].get('title'),
            'channelId': video['snippet'].get('channelId'),
            'description': video['snippet'].get('description'),
            'keywords': video['snippet'].get('keywords'),
            'publishedAt': video['snippet'].get('publishedAt').replace('T', ' ').replace('Z', ' '),
            'duration': video['contentDetails'].get('duration').replace('M', 'M ').replace('PT', ''),
            'thumbnail_url': yt.thumbnail_url,
            'tags': video['snippet'].get('tags'),
            'categoryId': video['snippet'].get('categoryId'),
            'viewCount': video['statistics'].get('viewCount'),
            'likeCount': video['statistics'].get('likeCount'),
            'commentCount': video['statistics'].get('commentCount'),
            'count': len(stream),
            'downloads': downloads
        }
    except KeyError:
        return False
