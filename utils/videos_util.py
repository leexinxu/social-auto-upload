import subprocess
import os
from datetime import datetime

def extract_cover_from_video(video_path, cover_image_path):
    # 生成时间戳
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    
    # 如果封面图像已存在，修改文件名以添加时间戳
    base, ext = os.path.splitext(cover_image_path)
    if os.path.exists(cover_image_path):
        cover_image_path = f"{base}_{timestamp}{ext}"

    # 使用 FFmpeg 从视频中提取封面
    command = [
        'ffmpeg',
        '-i', video_path,       # 输入视频文件
        '-ss', '00:00:01.000',  # 从视频的第1秒开始截取
        '-vframes', '1',        # 只提取一帧
        cover_image_path        # 输出封面图像路径
    ]

    # 使用 subprocess 运行 FFmpeg 命令
    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = process.communicate()

    if process.returncode != 0:
        # 处理错误情况
        raise RuntimeError(f"FFmpeg error: {stderr.decode()}")

    print(f"封面成功提取到 {cover_image_path}")
    return cover_image_path
