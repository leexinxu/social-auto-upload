# %%
import os
from datetime import datetime
import time
from pathlib import Path
import configparser
from xhs import XhsClient
from xhs_uploader.main import sign_local, beauty_print
import re
import json

# %%
def log(message):
    current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(f"{current_time} - {message}")

def find_videos(folder):
    dir_list = []
    for dir, _, files in os.walk(folder):
        if 'ok.json' in files and 'video.mp4' in files and 'xiaohongshu.json' not in files:
            dir_list.append(dir)
    return dir_list

# 上传视频到小红书
def upload(folder, xhs_client):
    log(f"上传视频到小红书 {folder=}")

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

    # 去除空格
    tags = [tag[:20].replace(" ", "") for tag in tags]

    # 打印视频文件名、标题和 hashtag
    print(f"视频文件名：{video_path}")
    print(f"标题：{title}")
    print(f"标签：{tags}")

    # 加入到标题 补充标题（xhs 可以填1000字不写白不写）
    tags_str = ' '.join(['#' + tag for tag in tags])

    note = xhs_client.create_video_note(title="", video_path=str(video_path),
                                        desc=f"{title}\n\n{description}\n\n{tags_str}",
                                        topics=None,
                                        is_private=False,
                                        post_time=None)

    beauty_print(note)

    with open(os.path.join(folder, 'xiaohongshu.json'), 'w', encoding='utf-8') as f:
        json.dump(note, f, ensure_ascii=False, indent=4)
    return True

# %%
# 每分钟检查一下是否有需要上传的视频，如果有，则上传
def check_up(src_dir):
    log(f"******* 启动上传到小红书脚本, 检查视频目录: {src_dir} *******")
    while True:
        log("检查是否有视频需要上传到小红书...")
        up_dir_list = find_videos(src_dir)
        log(f"找到需要上传小红书: {len(up_dir_list)}")

        if len(up_dir_list) > 0:
            
            config = configparser.RawConfigParser()
            config.read(Path(Path(__file__).parent.resolve() / "xhs_uploader" / "accounts.ini"))
            cookies = config['account1']['cookies']
            xhs_client = XhsClient(cookies, sign=sign_local, timeout=60)
            # auth cookie
            # 注意：该校验cookie方式可能并没那么准确
            try:
                xhs_client.get_video_first_frame_image_id("3214")
            except:
                print("cookie 失效")
                exit()

            for up_dir in up_dir_list:
                try:
                  # 上传到小红书视频
                  upload(up_dir, xhs_client)
                except Exception as e:
                  log(f"上传小红书异常 {up_dir}: {e}")
                  with open(os.path.join(up_dir, 'xiaohongshu.json'), 'w', encoding='utf-8') as f:
                    json.dump({"e": str(e)}, f, ensure_ascii=False, indent=4)
                
                # 防止提交过快
                log("防止提交过快，等待1分钟上传下一个。。。")
                time.sleep(60)

        # 等待 60 秒再检查
        log("等待10分钟再检查。。。")
        time.sleep(600)

# %%
# 启动自动上传
src_dir = '/Volumes/Data/AI/YouDub-webui/videos_20240808'
check_up(src_dir)


