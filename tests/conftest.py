import nonebot
import pytest

# Import adapters
from nonebot.adapters.onebot.v11 import Adapter as ONEBOT_V11Adapter
from nonebot.adapters.onebot.v12 import Adapter as ONEBOT_V12Adapter


@pytest.fixture(scope="session", autouse=True)
def load_bot():
    # Load adapters
    driver = nonebot.get_driver()
    driver.register_adapter(ONEBOT_V11Adapter)
    driver.register_adapter(ONEBOT_V12Adapter)
    # Load plugins
    nonebot.load_from_toml("pyproject.toml")
