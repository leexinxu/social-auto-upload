import asyncio
from pathlib import Path

from conf import BASE_DIR
from xigua_uploader.main import xigua_setup

if __name__ == '__main__':
    account_file = Path(BASE_DIR / "xigua_uploader" / "account.json")
    cookie_setup = asyncio.run(xigua_setup(str(account_file), handle=True))
