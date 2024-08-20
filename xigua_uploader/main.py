# -*- coding: utf-8 -*-
from datetime import datetime

from playwright.async_api import Playwright, async_playwright
import os
import asyncio

from conf import LOCAL_CHROME_PATH
from utils.base_social_media import set_init_script
from utils.log import xigua_logger
from utils.videos_util import extract_cover_from_video

import re


async def cookie_auth(account_file):
    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch(headless=True)
        context = await browser.new_context(storage_state=account_file)
        context = await set_init_script(context)
        # 创建一个新的页面
        page = await context.new_page()
        # 访问指定的 URL
        await page.goto("https://studio.ixigua.com/upload")
        # 2024.06.17 抖音创作者中心改版
        if await page.get_by_text('登录 / 注册').count():
            print("[+] 等待5秒 cookie 失效")
            return False
        else:
            print("[+] cookie 有效")
            return True


async def xigua_setup(account_file, handle=False):
    if not os.path.exists(account_file) or not await cookie_auth(account_file):
        if not handle:
            # Todo alert message
            return False
        xigua_logger.info('[+] cookie文件不存在或已失效，即将自动打开浏览器，请扫码登录，登陆后会自动生成cookie文件')
        await xigua_cookie_gen(account_file)
    return True


async def xigua_cookie_gen(account_file):
    async with async_playwright() as playwright:
        options = {
            'headless': False
        }
        # Make sure to run headed.
        browser = await playwright.chromium.launch(**options)
        # Setup context however you like.
        context = await browser.new_context()  # Pass any options
        context = await set_init_script(context)
        # Pause the page, and start recording manually.
        page = await context.new_page()
        await page.goto("https://studio.ixigua.com/")
        await page.pause()
        # 点击调试器的继续，保存cookie
        await context.storage_state(path=account_file)


class XiGuaVideo(object):
    def __init__(self, title, file_path, tags, publish_date: datetime, account_file, cover, summary):
        self.title = title  # 视频标题
        self.file_path = file_path
        self.tags = tags
        self.publish_date = publish_date
        self.account_file = account_file
        self.date_format = '%Y年%m月%d日 %H:%M'
        self.local_executable_path = LOCAL_CHROME_PATH
        self.cover = cover
        self.summary = summary

    async def set_schedule_time_xigua(self, page, publish_date):
        # 选择包含特定文本内容的 label 元素
        label_element = page.locator("label.radio--4Gpx6:has-text('定时发布')")
        # 在选中的 label 元素下点击 checkbox
        await label_element.click()
        await asyncio.sleep(1)
        publish_date_hour = publish_date.strftime("%Y-%m-%d %H:%M")

        await asyncio.sleep(1)
        await page.locator('.semi-input[placeholder="日期和时间"]').click()
        await page.keyboard.press("Control+KeyA")
        await page.keyboard.type(str(publish_date_hour))
        await page.keyboard.press("Enter")

        await asyncio.sleep(1)

    async def handle_upload_error(self, page):
        xigua_logger.info('视频出错了，重新上传中')
        await page.locator('div.progress-div [class^="upload-btn-input"]').set_input_files(self.file_path)

    async def upload(self, playwright: Playwright) -> None:
        # 使用 Chromium 浏览器启动一个浏览器实例
        if self.local_executable_path:
            browser = await playwright.chromium.launch(headless=False, executable_path=self.local_executable_path)
        else:
            browser = await playwright.chromium.launch(headless=True)
        # 创建一个浏览器上下文，使用指定的 cookie 文件
        context = await browser.new_context(storage_state=f"{self.account_file}")
        context = await set_init_script(context)

        # 创建一个新的页面
        page = await context.new_page()
        # 访问指定的 URL
        await page.goto("https://studio.ixigua.com/upload")
        xigua_logger.info(f'[+]正在上传-------{self.title}.mp4')
        # 等待页面跳转到指定的 URL，没进入，则自动等待到超时
        xigua_logger.info(f'[-] 正在打开主页...')
        await page.wait_for_url("https://studio.ixigua.com/upload")
        # 点击 "上传视频" 按钮
        await page.locator("input[type='file']").set_input_files(self.file_path)

        # 等待页面跳转到指定的 URL
        while True:
            # 判断是是否进入视频发布页面，没进入，则自动等待到超时
            try:
                await page.wait_for_url(
                    "https://studio.ixigua.com/upload")
                break
            except:
                xigua_logger.info(f'  [-] 正在等待进入视频发布页面...')
                await asyncio.sleep(0.1)

        # 填充标题和话题
        # 检查是否存在包含输入框的元素
        # 这里为了避免页面变化，故使用相对位置定位：作品标题父级右侧第一个元素的input子元素
        if len(self.title) < 5:
            self.title = "【中配】破浪"  # 标题小于5个字符
        await asyncio.sleep(1)
        xigua_logger.info(f'  [-] 正在填充标题和话题...')
        # 使用更具体的选择器或选择特定的元素
        title_containers = page.locator("div.public-DraftStyleDefault-block")
        # 选择第一个匹配的标题输入框
        if await title_containers.count() > 0:
            title_container = title_containers.nth(0)
            await title_container.click()
            # 清除现有内容并输入新标题
            await page.keyboard.press("Control+KeyA")
            await page.keyboard.press("Backspace")
            await page.keyboard.type(self.title[:30])
        else:
            xigua_logger.error("标题输入框未找到")

        # 使用更具体的选择器定位输入框
        tag_input = page.locator('input[placeholder="输入合适的话题"]')
        if await tag_input.count() > 0:
            # 确保输入框获取焦点
            await tag_input.click()
            # 遍历话题标签，并依次输入
            for index, tag in enumerate(self.tags[:10], start=1):
                await page.keyboard.type(f"#{tag}")  # 输入话题
                await page.wait_for_timeout(1000)  # 等待 1000 毫秒以确保输入稳定
                await page.keyboard.press("Enter")  # 按下 Enter 键以添加话题

            xigua_logger.info(f'总共添加{len(self.tags)}个话题')

        while True:
            # 判断是否显示“上传成功”的状态，若无则继续等待
            try:
                # 使用新选择器定位上传成功状态
                success_count = await page.locator('div.status:has-text("上传成功")').count()
                if success_count > 0:
                    xigua_logger.success("  [-] 视频上传完毕")
                    break
                else:
                    xigua_logger.info("  [-] 正在上传视频中...")
                    await asyncio.sleep(2)

                    # 检查上传失败的状态，并进行重试
                    if await page.locator('div.progress-div > div:has-text("上传失败")').count():
                        xigua_logger.error("  [-] 发现上传出错了... 准备重试")
                        await self.handle_upload_error(page)
            except Exception as e:
                xigua_logger.info(f"  [-] 正在上传视频中... 错误: {str(e)}")
                await asyncio.sleep(2)

        
        # 检查封面是否为 None 或者文件是否不存在
        if not self.cover or not os.path.exists(self.cover):
            # 如果 self.cover 为空或文件不存在，从视频中提取封面
            self.cover = extract_cover_from_video(self.file_path, cover_image_path = os.path.splitext(self.file_path)[0] + '.png')

        # 定位“上传封面”按钮并点击
        upload_button = page.locator('div.m-xigua-upload')
        await upload_button.click()
        # 点击“本地上传”按钮
        local_upload_button = page.locator('li:has-text("本地上传")')
        await local_upload_button.click()
        # 等待文件上传输入框出现
        file_input = page.locator("input[type='file'][accept='image/jpg,image/jpeg,image/png,image/x-png,image/webp']")
        # 使用 file_input.set_files 方法上传封面图片
        await file_input.set_input_files(self.cover)
        # 等待“完成裁剪”按钮出现并点击
        await page.wait_for_timeout(1000)  # 等待 1000 毫秒以确保输入稳定
        complete_crop_button = page.locator('div.clip-btn-content:has-text("完成裁剪")')
        # 禁用的“确定”按钮
        confirm_button_disabled = page.locator('button.btn-l.btn-sure.ml16.disabled:has-text("确定")')
        # 检查“完成裁剪”按钮是否存在
        if await complete_crop_button.count() > 0 and await confirm_button_disabled.count() > 0:
            # 如果存在，点击“完成裁剪”按钮
            await complete_crop_button.click()
        # 等待“确定”按钮出现并点击
        confirm_button = page.locator('button.btn-l.btn-sure.ml16:has-text("确定")')
        await confirm_button.click()
        # 或者点击红色“确定”按钮
        red_confirm_button = page.locator('button.m-button.red:has-text("确定")')
        await red_confirm_button.click()
        await page.wait_for_timeout(2000)  # 等待 2秒以确保输入稳定
        xigua_logger.success("  [-] 封面上传成功！")

        # 定位包含“原创”文本的 label 元素
        original_option = page.locator('label.byte-radio:has-text("原创")')
        if await original_option.count() > 0:
            # 点击选项以选择“原创”
            await original_option.click()

        # 输入简介
        # 定位内容可编辑区域
        summary = page.locator('div.public-DraftEditorPlaceholder-inner:has-text("请填写视频简介")')
        editors = page.locator('div.public-DraftEditor-content')
        # 确保找到的元素只有一个或选择第一个
        if await editors.count() > 0 and await summary.count() > 0:
            editor = editors.nth(1)  # 使用 nth 方法选择第二个元素 20240803
            # 清空内容编辑区域中的现有内容
            await editor.click()
            await page.keyboard.press("Control+A")  # 选择所有文本
            await page.keyboard.press("Backspace")  # 删除所有文本
            # 输入新的内容
            await editor.type(self.summary[:400])

            # 定位“添加至合集”按钮并点击
            add_to_collection_button = page.locator('div.add-button:has-text("添加至合集")')
            if await add_to_collection_button.count() > 0:
                await add_to_collection_button.click()
                # 定位“中文配音”项
                series_item = page.locator('li.m-series-item:has-text("【中文配音】")')
                # 从 series_item 内部找到 input 元素
                input_element = series_item.locator('input[type="radio"]')
                # 检查 input 元素是否被禁用
                is_disabled = await input_element.is_disabled()
                if is_disabled:
                    # 定位 <footer> 元素
                    footer_element = page.locator('footer.m-add-to-series-modal-footer')
                    # 在 <footer> 内部定位带有“取消”文本的按钮
                    cancel_button = footer_element.locator('button:has-text("取消")')
                    # 点击“取消”按钮
                    await cancel_button.click()
                else:
                    # 点击“中文配音”项
                    await series_item.click()
                    # 定位并点击确认按钮
                    confirm_button = page.locator('button:has-text("确认")')
                    await confirm_button.click()


        # 判断视频是否发布成功
        max_attempts = 10  # 最大尝试次数
        attempts = 0  # 当前尝试次数

        while True:
            # 检查是否出现“发文频繁”的提示
            rate_limit_message = await page.get_by_text("发文频繁").count()
            if rate_limit_message > 0:
                raise Exception("发文频繁")

            # 判断视频是否发布成功
            try:
                publish_button = page.get_by_role('button', name="发布", exact=True)
                if await publish_button.count():
                    await publish_button.click()
                
                await page.wait_for_url(re.compile(r"https://studio\.ixigua\.com/content.*"),
                                        timeout=3000)  # 如果自动跳转到作品页面，则代表发布成功
                xigua_logger.success("  [-]视频发布成功")
                break
            except:
                attempts += 1
                if attempts >= max_attempts:
                    raise Exception("发布视频尝试次数过多，可能存在问题")
                
                xigua_logger.info(f"  [-] 视频正在发布中... 尝试次数: {attempts}/{max_attempts}")
                await page.screenshot(full_page=True)
                await asyncio.sleep(0.5)


        await context.storage_state(path=self.account_file)  # 保存cookie
        xigua_logger.success('  [-]cookie更新完毕！')
        await asyncio.sleep(2)  # 这里延迟是为了方便眼睛直观的观看
        # 关闭浏览器上下文和浏览器实例
        await context.close()
        await browser.close()

    async def main(self):
        async with async_playwright() as playwright:
            await self.upload(playwright)


