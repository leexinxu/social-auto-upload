# %%
import os
from datetime import datetime
import glob
import shutil
import time
import asyncio
from pathlib import Path
import configparser
from xhs import XhsClient
from xhs_uploader.main import sign_local, beauty_print
import re

# %%
def log(message):
    current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(f"{current_time} - {message}")

# %%
def find_chinese_subbed_videos(base_folder):
    file_list = []
    
    # 遍历第一层文件夹
    for root, dirs, files in os.walk(base_folder):
        # 查找当前目录下符合模式的文件
        for file in glob.glob(os.path.join(root, '【中配】*.mp4')):
            file_list.append(os.path.abspath(file))
        
        # 遍历第二层文件夹
        for sub_dir in dirs:
            sub_dir_path = os.path.join(root, sub_dir)
            for file in glob.glob(os.path.join(sub_dir_path, '【中配】*.mp4')):
                file_list.append(os.path.abspath(file))
        
        # 只遍历两级，跳过子目录的子目录
        break
    
    return file_list

# %%
def move_folder(src_folder, dst_dir):
    try:
        # 创建目标目录（如果不存在）
        if not os.path.exists(dst_dir):
            os.makedirs(dst_dir)
        
        # 移动文件夹
        shutil.move(src_folder, os.path.join(dst_dir, os.path.basename(src_folder)))
        log(f"Moved: {src_folder} to {dst_dir}")
    except Exception as e:
        log(f"Error moving folder {src_folder}: {e}")

# %%
# 上传视频
def upload(filepath, xhs_client):
    if not os.path.exists(filepath):
        print(f'{filepath} not exists')
        return

    # 标题使用 文件名, 文件名示例：【中配】人工智能【AI】
    title = os.path.splitext(os.path.basename(filepath))[0]
    
    tags = ['破浪', '科技', '未来', 'AI', 'AGI']

    # 打印视频文件名、标题和 hashtag
    print(f"视频文件名：{filepath}")
    print(f"标题：{title}")
    print(f"Hashtag：{tags}")

    # 加入到标题 补充标题（xhs 可以填1000字不写白不写）
    tags_str = ' '.join(['#' + tag for tag in tags])

    # 短标题
    # 使用正则表达式提取中间部分
    pattern = r"】(.*?)【"
    match = re.search(pattern, title)
    # 获取匹配的内容
    sub_title = match.group(1) if match else title

    note = xhs_client.create_video_note(title=sub_title[:20], video_path=str(filepath),
                                        desc=title + tags_str,
                                        topics=None,
                                        is_private=False,
                                        post_time=None)

    beauty_print(note)

# %%
# 每分钟检查一下是否有需要上传的视频，如果有，则上传
def check_up(src_dir, dst_dir):
    log("******* Start Auto Video XHS Upload *******")
    while True:
        log("Checking for new videos...")
        # 获取目录中两级的【中配】*.mp4文件
        mp4_files = find_chinese_subbed_videos(src_dir)
        log(f"Get new videos : {len(mp4_files)}")

        if len(mp4_files) > 0:
            
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

            for mp4_file in mp4_files:
                try:
                  # 上传视频
                  upload(mp4_file, xhs_client)
                except Exception as e:
                  log(f"Error uploading video {mp4_file}: {e}")
                
                # 上传完移动文件夹到TranslationCompletedUploadBilibiliMove
                move_folder(os.path.dirname(mp4_file), dst_dir)

                # 防止提交过快
                log("Waiting for 60 seconds before next upload...")
                time.sleep(60)

        # 等待 60 秒再检查
        log("Waiting for 60 seconds before next check...")
        time.sleep(60)

# %%
# 启动自动上传
src_dir = '/Volumes/Data/VideoTranslation/TranslationCompletedUploadDouyinMove'
dst_dir = '/Volumes/Data/VideoTranslation/TranslationCompletedUploadXHSMove'
check_up(src_dir, dst_dir)


