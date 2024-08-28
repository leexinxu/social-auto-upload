# %%
import os
from datetime import datetime
import time
import asyncio
from pathlib import Path
from xigua_uploader.main import xigua_setup, XiGuaVideo
import json

# %%
def log(message):
    current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(f"{current_time} - {message}")

# %%
def is_landscape(info_path):
    """检查视频信息中是否为横版视频（即宽度大于高度）。"""
    try:
        with open(info_path, 'r', encoding='utf-8') as f:
            info = json.load(f)
            width = info.get('width')
            height = info.get('height')
            duration = info.get('duration')
            # 检查宽高是否存在且宽度大于高度，且视频时长大于等于 60 秒
            if width and height and duration:
                return width > height and duration >= 60
    except (FileNotFoundError, json.JSONDecodeError):
        return False  # 如果文件不存在或解析错误，则视为不是横版
    return False

# %%
def find_videos(folder):
    dir_list = []
    for dir, _, files in os.walk(folder):
        if 'ok.json' in files and 'video.mp4' in files and 'douyin.json' not in files and 'download.info.json' in files:
            info_path = os.path.join(dir, 'download.info.json')
            if is_landscape(info_path):  # 使用 JSON 文件检查是否为横版
                dir_list.append(dir)
    return dir_list

# %%
# 上传视频到西瓜
def upload(folder, account_file):
    log(f"使用 {account_file=}")
    log(f"上传视频到西瓜 {folder=}")

    # 检查cookie
    cookie_setup = asyncio.run(xigua_setup(account_file, handle=False))

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
    description = f'{summary["summary"]}\n\n{summary["author"]}'

    title = f'【中配】{summary["title"]}【{title_English}】'

    # 如果标题大于30个字符会被截断，把标题也放简介里
    if len(title) > 30:
        description = f'{title}\n\n{description}'
        # 标题去掉英文标题，截取到最后一个 '【' 之前的内容，去掉小于5就不去了
        if len(title[:title.rfind('【')].strip()) >= 5:
            title = title[:title.rfind('【')].strip()

    # 标题小于5个字符
    if len(title) < 5:
        title = "【中配】破浪"

    # 去除空格并获取前10个标签, 且每个标签长度不超过20
    tags = [tag[:20].replace(" ", "") for tag in tags][:10]

    # 打印视频文件名、标题和 hashtag
    print(f"视频文件名：{video_path}")
    print(f"标题：{title}")
    print(f"标签：{tags}")
    print(f"简介：{description}")
    print(f"视频封面：{cover_path}")
    app = XiGuaVideo(title, video_path, tags, 0, account_file, cover_path, description)
    asyncio.run(app.main(), debug=False)

    with open(os.path.join(folder, 'douyin.json'), 'w', encoding='utf-8') as f:
        json.dump({}, f, ensure_ascii=False, indent=4)
    return True

# %%
# 每分钟检查一下是否有需要上传的视频，如果有，则上传
def check_up(src_dir, account_files):
    log(f"******* 启动上传到西瓜脚本, 检查视频目录: {src_dir} *******")
    account_index = 0

    while True:
        log("检查是否有视频需要上传到西瓜...")
        up_dir_list = find_videos(src_dir)
        log(f"找到需要上传西瓜: {len(up_dir_list)}")

        for up_dir in up_dir_list:
            success = False
            retry_count = 0

            while not success and retry_count < len(account_files):
                # 轮询选择账号文件
                account_file = account_files[account_index]

                try:
                    # 上传视频到西瓜
                    upload(up_dir, account_file)
                    success = True  # 上传成功
                except Exception as e:
                    log(f"账号 {account_file} 上传失败：{e}")

                # 切换到下一个账号文件
                account_index = (account_index + 1) % len(account_files)
                retry_count += 1

            if not success:
                log(f"视频 {up_dir} 上传失败，所有账号均尝试过。")

        log("等待10分钟再检查。。。")
        time.sleep(60*10)

# %%
# 启动自动上传
BASE_DIR = Path(__file__).parent.resolve()
account_files = [Path(BASE_DIR / "xigua_uploader" / "account_polang.json"), 
                 Path(BASE_DIR / "xigua_uploader" / "account_changfeng.json")]
src_dir = '/Volumes/Data/AI/YouDub-webui/videos_20240821'
check_up(src_dir, account_files)



