# %%
import os
from datetime import datetime
import time
import asyncio
from pathlib import Path
from douyin_uploader.main import douyin_setup, DouYinVideo
import json

# %%
def log(message):
    current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(f"{current_time} - {message}")

# %%
def find_videos(folder):
    dir_list = []
    for dir, _, files in os.walk(folder):
        if 'ok.json' in files and 'video.mp4' in files and 'douyin.json' not in files:
            dir_list.append(dir)
    return dir_list

# %%
# 上传视频到抖音
def upload(folder, account_file):
    log(f"上传视频到抖音 {folder=}")

    video_path = os.path.join(folder, 'video.mp4')
    cover_path = os.path.join(folder, 'video.png')

    # Load summary data
    with open(os.path.join(folder, 'summary.json'), 'r', encoding='utf-8') as f:
        summary = json.load(f)
    summary['title'] = summary['title'].replace('视频标题：', '').strip()
    summary['summary'] = summary['summary'].replace(
        '视频摘要：', '').replace('视频简介：', '').strip()
    tags = summary.get('tags', [])
    if not isinstance(tags, list):
        tags = []
    
    with open(os.path.join(folder, 'download.info.json'), 'r', encoding='utf-8') as f:
        data = json.load(f)
    title_English = data['title']
    webpage_url = data['webpage_url']
    description = f'{summary["summary"]}\n\n{summary["author"]}\n\n{webpage_url}'

    title = f'【中配】{summary["title"]}【{title_English}】'

    title = f'{title}\n\n {description}'

    # 去除空格并获取前5个标签
    tags = [tag.replace(" ", "") for tag in tags][:5]

    # 打印视频文件名、标题和 hashtag
    print(f"视频文件名：{video_path}")
    print(f"标题：{title}")
    print(f"标签：{tags}")
    app = DouYinVideo(title, video_path, tags, 0, account_file)
    asyncio.run(app.main(), debug=False)

    with open(os.path.join(folder, 'douyin.json'), 'w', encoding='utf-8') as f:
        json.dump({}, f, ensure_ascii=False, indent=4)
    return True

# %%
# 每分钟检查一下是否有需要上传的视频，如果有，则上传
def check_up(src_dir, account_file):
    log(f"******* 启动上传到抖音脚本, 检查视频目录: {src_dir} *******")
    while True:
        log("检查是否有视频需要上传到抖音...")
        up_dir_list = find_videos(src_dir)
        log(f"找到需要上传抖音: {len(up_dir_list)}")
        for up_dir in up_dir_list:
            # 上传视频到抖音
            upload(up_dir, account_file)

            # 防止提交过快
            log("防止提交过快，等待1分钟上传下一个。。。")
            time.sleep(60)

        log("等待10分钟再检查。。。")
        time.sleep(60*10)

# %%
# 启动自动上传
BASE_DIR = Path(__file__).parent.resolve()
account_file = Path(BASE_DIR / "douyin_uploader" / "account.json")
src_dir = '/Volumes/Data/AI/YouDub-webui/videos'
check_up(src_dir, account_file)


