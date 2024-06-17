# %%
import os
from datetime import datetime
import glob
import shutil
import time
import asyncio
from pathlib import Path
from douyin_uploader.main import douyin_setup, DouYinVideo

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
# 上传视频到抖音
def upload(filepath, account_file):
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
    app = DouYinVideo(title, filepath, tags, 0, account_file)
    asyncio.run(app.main(), debug=False)

# %%
# 每分钟检查一下是否有需要上传的视频，如果有，则上传
def check_up(src_dir, dst_dir, account_file):
    log("******* Start Auto Video Douyin Upload *******")
    while True:
        log("Checking for new videos...")
        # 获取目录中两级的【中配】*.mp4文件
        mp4_files = find_chinese_subbed_videos(src_dir)
        log(f"Get new videos : {len(mp4_files)}")
        for mp4_file in mp4_files:
            # 上传视频到抖音
            upload(mp4_file, account_file)
            
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
BASE_DIR = Path(__file__).parent.resolve()
account_file = Path(BASE_DIR / "douyin_uploader" / "account.json")
src_dir = '/Volumes/Data/VideoTranslation/TranslationCompletedUploadBilibiliMove'
dst_dir = '/Volumes/Data/VideoTranslation/TranslationCompletedUploadDouyinMove'
check_up(src_dir, dst_dir, account_file)


