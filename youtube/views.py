from django.shortcuts import render, redirect

from youtube.utils import get_video_data


def index(request):
    return render(request, 'youtube/index.html')


async def download(request):
    if request.method == 'POST':
        url = request.POST['url']
        yt = await get_video_data(url)
        context = {
            'youtube': yt,
        }
        return render(request, 'youtube/download.html', context)
    return redirect('index')
