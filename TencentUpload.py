# %%
import os
from datetime import datetime
import glob
import shutil
import time
import asyncio
from pathlib import Path
from tencent_uploader.main import weixin_setup, TencentVideo
from utils.constant import TencentZoneTypes
from playwright.async_api import Playwright, async_playwright
from utils.base_social_media import set_init_script

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
def upload(filepath, account_file):
    if not os.path.exists(filepath):
        print(f'{filepath} not exists')
        return

    # 标题使用 文件名, 文件名示例：【中配】人工智能【AI】
    title = os.path.splitext(os.path.basename(filepath))[0]
    tags = ['破浪', '科技', '未来', 'AI', 'AGI']
    category = TencentZoneTypes.TECHNOLOGY.value  # 标记原创需要否则不需要传

    # 打印视频文件名、标题和 hashtag
    print(f"视频文件名：{filepath}")
    print(f"标题：{title}")
    print(f"Hashtag：{tags}")
    app = TencentVideo(title, filepath, tags, 0, account_file, category=None)
    asyncio.run(app.main(), debug=False)

# %%
# 更新cookie
async def update_cookie_playwright(account_file):
    async with async_playwright() as playwright:
        # 使用 Chromium (这里使用系统内浏览器，用chromium 会造成h264错误
        browser = await playwright.chromium.launch(headless=False, executable_path='/Applications/Google Chrome.app/Contents/MacOS/Google Chrome')
        # 创建一个浏览器上下文，使用指定的 cookie 文件
        context = await browser.new_context(storage_state=f"{account_file}")
        context = await set_init_script(context)

        # 创建一个新的页面
        page = await context.new_page()
        # 访问指定的 URL
        await page.goto("https://channels.weixin.qq.com/platform/post/create")
        # 等待页面完全加载完成
        await page.wait_for_load_state("networkidle")  # "load"、"domcontentloaded" 或 "networkidle" 都可以选择
        await context.storage_state(path=f"{account_file}")  # 保存cookie
        log('cookie更新完毕！')
        # 关闭浏览器上下文和浏览器实例
        await context.close()
        await browser.close()


# %%
# 更新cookie
def update_cookie(account_file = Path(Path(__file__).parent.resolve() / "tencent_uploader" / "account.json")):
    # 获取文件的最后修改时间
    last_modified_time = os.path.getmtime(account_file)
    # 获取当前时间
    current_time = time.time()
    # 计算时间差
    time_difference = current_time - last_modified_time
    # 判断时间差是否超过一个小时
    if time_difference > 3600:
        # 更新cookie
        log("Updating cookie...")
        asyncio.run(update_cookie_playwright(account_file), debug=False)
        return True
    else:
        log("No need to update cookie")
        return False

# %%
# 每分钟检查一下是否有需要上传的视频，如果有，则上传
def check_up(src_dir, dst_dir, account_file):
    log("******* Start Auto Video Tencent Upload *******")
    while True:
        log("Checking for new videos...")
        # 获取目录中两级的【中配】*.mp4文件
        mp4_files = find_chinese_subbed_videos(src_dir)
        log(f"Get new videos : {len(mp4_files)}")

        if len(mp4_files) > 0:
            # 上传视频
            for mp4_file in mp4_files:
                # 上传视频
                upload(mp4_file, account_file)
                
                # 上传完移动文件夹到TranslationCompletedUploadBilibiliMove
                move_folder(os.path.dirname(mp4_file), dst_dir)

                # 防止提交过快
                log("Waiting for 60 seconds before next upload...")
                time.sleep(60)
        #else:
            # 更新cookie
            #update_cookie(account_file)

        # 等待 60 秒再检查
        log("Waiting for 60 seconds before next check...")
        time.sleep(60)

# %%
# 启动自动上传
BASE_DIR = Path(__file__).parent.resolve()
account_file = Path(BASE_DIR / "tencent_uploader" / "account.json")
src_dir = '/Volumes/Data/VideoTranslation/TranslationCompletedUploadXHSMove'
dst_dir = '/Volumes/Data/VideoTranslation/TranslationCompletedUploadTencentMove'
check_up(src_dir, dst_dir, account_file)


