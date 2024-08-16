import asyncio
from pathlib import Path

from conf import BASE_DIR
from xigua_uploader.main import xigua_setup, XiGuaVideo
from utils.files_times import generate_schedule_time_next_day, get_title_and_hashtags


if __name__ == '__main__':
    filepath = Path(BASE_DIR) / "videos"
    account_file = Path(BASE_DIR / "xigua_uploader" / "account.json")
    # 获取视频目录
    folder_path = Path(filepath)
    # 获取文件夹中的所有文件
    files = list(folder_path.glob("*.mp4"))
    file_num = len(files)
    publish_datetimes = generate_schedule_time_next_day(file_num, 1, daily_times=[16])
    cookie_setup = asyncio.run(xigua_setup(account_file, handle=False))
    cover = "videos/video.png"
    summary = "简介。。。"
    for index, file in enumerate(files):
        title, tags = get_title_and_hashtags(str(file))
        # 打印视频文件名、标题和 hashtag
        print(f"视频文件名：{file}")
        print(f"标题：{title}")
        print(f"Hashtag：{tags}")
        print(f"封面：{cover}")
        print(f"简介：{summary}")
        app = XiGuaVideo(title, file, tags, publish_datetimes[index], account_file, cover, summary)
        asyncio.run(app.main(), debug=False)