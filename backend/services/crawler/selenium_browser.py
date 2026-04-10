#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Selenium 浏览器管理 - 自动处理 Cloudflare/年龄验证
"""

import asyncio
import re
import time
import random
import logging
from typing import Optional, List, Dict, Any
from pathlib import Path
from dataclasses import dataclass
import os

logger = logging.getLogger(__name__)

# 目标站点配置
SEHUATANG_URL = "https://www.sehuatang.org"
AGE_VERIFY_URL = "https://www.sehuatang.org/hack.php?H_name=ageverify"


@dataclass
class BrowserConfig:
    """浏览器配置"""
    headless: bool = True
    user_agent: str = (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    )
    page_load_timeout: int = 30
    implicit_wait: int = 10
    viewport_width: int = 1920
    viewport_height: int = 1080


class SeleniumBrowser:
    """
    Selenium 浏览器管理器
    
    功能:
    - 全局单例浏览器实例
    - 自动处理 Cloudflare 验证
    - 自动处理年龄验证
    - 自动维护 Cookie
    - 获取页面源码
    """
    
    _instance: Optional['SeleniumBrowser'] = None
    _lock = asyncio.Lock()
    
    def __new__(cls, *args, **kwargs):
        """单例模式"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self, base_url: str = SEHUATANG_URL, config: BrowserConfig = None):
        if self._initialized:
            return
        
        self.base_url = base_url
        self.config = config or BrowserConfig()
        self.driver = None
        self._initialized = True
        self._is_running = False
        self._cf_check_count = 0
        self._last_page_source = ""
        
        # Cookie 存储路径
        self.cookie_dir = Path("data/cookies")
        self.cookie_dir.mkdir(parents=True, exist_ok=True)
        self.cookie_file = self.cookie_dir / "browser_cookies.json"
    
    async def init_browser(self) -> bool:
        """
        初始化浏览器

        Returns:
            是否初始化成功
        """
        if self._is_running and self.driver:
            return True

        try:
            from selenium import webdriver
            from selenium.webdriver.chrome.service import Service
            from selenium.webdriver.chrome.options import Options
            from selenium.webdriver.common.by import By
            from selenium.webdriver.support.ui import WebDriverWait
            from selenium.webdriver.support import expected_conditions as EC

            # 配置 Chrome 选项
            options = Options()

            if self.config.headless:
                options.add_argument("--headless=new")

            options.add_argument(f"--user-agent={self.config.user_agent}")
            options.add_argument(f"--window-size={self.config.viewport_width},{self.config.viewport_height}")
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            options.add_argument("--disable-gpu")
            options.add_argument("--disable-blink-features=AutomationControl")
            options.add_argument("--disable-extensions")
            options.add_argument("--disable-plugins")
            options.add_argument("--ignore-certificate-errors")
            options.add_argument("--ignore-ssl-errors")

            # Linux 无头模式特殊处理
            import platform
            if platform.system() == "Linux":
                options.add_argument("--disable-setuid-sandbox")
                options.add_argument("--single-process")
                # 尝试使用 Xvfb 或 Chrome 内置无头模式
                if self.config.headless:
                    options.add_argument("--headless=new")

            # Windows 特殊处理
            if platform.system() == "Windows":
                # Windows 需要关闭一些选项
                options.add_argument("--disable-features=TranslateUI")
                options.add_argument("--disable-ipc-flooding-protection")

            # 禁用 webdriver 特征
            options.add_experimental_option("excludeSwitches", ["enable-automation"])
            options.add_experimental_option('useAutomationExtension', False)

            # 尝试自动检测 Chrome 路径
            chrome_binary = self._find_chrome_binary()
            if chrome_binary:
                options.binary_location = chrome_binary
                logger.info(f"使用 Chrome: {chrome_binary}")

            # 初始化 driver
            try:
                service = Service()
                self.driver = webdriver.Chrome(service=service, options=options)
            except Exception as e:
                logger.warning(f"直接启动失败，尝试其他方式: {e}")
                # 尝试使用 webdriver-manager
                try:
                    from webdriver_manager.chrome import ChromeDriverManager
                    service = Service(ChromeDriverManager().install())
                    self.driver = webdriver.Chrome(service=service, options=options)
                except Exception as e2:
                    logger.warning(f"webdriver-manager 也失败: {e2}")
                    # 最后的尝试
                    self.driver = webdriver.Chrome(options=options)

            # 设置超时
            self.driver.set_page_load_timeout(self.config.page_load_timeout)
            self.driver.implicitly_wait(self.config.implicit_wait)

            # 移除 webdriver 属性
            self.driver.execute_script(
                "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
            )

            self._is_running = True
            logger.info("Selenium 浏览器初始化成功")

            # 加载保存的 Cookie
            await self._load_cookies()

            return True

        except ImportError as e:
            logger.error(f"Selenium 未安装: {e}")
            logger.error("请运行: pip install selenium")
            return False
        except Exception as e:
            logger.error(f"浏览器初始化失败: {e}")
            logger.error("如果是首次使用，请运行安装脚本: bash scripts/install_selenium.sh")
            return False

    def _find_chrome_binary(self) -> Optional[str]:
        """自动查找 Chrome 可执行文件路径"""
        import platform
        import os

        system = platform.system()

        # 1. 先检查环境变量
        chrome_env = os.environ.get("CHROME_BIN") or os.environ.get("GOOGLE_CHROME_BIN")
        if chrome_env and os.path.exists(chrome_env):
            return chrome_env

        if system == "Linux":
            # Linux 常见路径
            linux_paths = [
                "/usr/bin/google-chrome",
                "/usr/bin/google-chrome-stable",
                "/usr/bin/chromium",
                "/usr/bin/chromium-browser",
                "/snap/bin/chromium",
                "/opt/google/chrome/chrome",
            ]
            for path in linux_paths:
                if os.path.exists(path):
                    return path

        elif system == "Darwin":  # macOS
            macos_paths = [
                "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
                "/Applications/Chromium.app/Contents/MacOS/Chromium",
            ]
            for path in macos_paths:
                if os.path.exists(path):
                    return path

        elif system == "Windows":
            import glob
            # Windows 常见路径
            windows_paths = [
                os.path.join(os.environ.get("ProgramFiles", ""), "Google\\Chrome\\Application\\chrome.exe"),
                os.path.join(os.environ.get("ProgramFiles(x86)", ""), "Google\\Chrome\\Application\\chrome.exe"),
                os.path.join(os.environ.get("LocalAppData", ""), "Google\\Chrome\\Application\\chrome.exe"),
            ]
            for path in windows_paths:
                if os.path.exists(path):
                    return path

            # 也检查 PATH
            for path in os.environ.get("PATH", "").split(os.pathsep):
                chrome_path = os.path.join(path, "chrome.exe")
                if os.path.exists(chrome_path):
                    return chrome_path

        return None
    
    async def goto(self, url: str, wait_after: float = 2.0) -> bool:
        """
        导航到指定 URL
        
        Args:
            url: 目标 URL
            wait_after: 加载后等待时间
            
        Returns:
            是否成功
        """
        if not self._is_running or not self.driver:
            if not await self.init_browser():
                return False
        
        try:
            logger.debug(f"导航到: {url}")
            self.driver.get(url)
            await asyncio.sleep(wait_after)
            
            # 检查并处理验证
            await self._check_and_handle_verification()
            
            return True
            
        except Exception as e:
            logger.error(f"导航失败: {url}, {e}")
            return False
    
    async def _check_and_handle_verification(self):
        """检查并处理各种验证"""
        # 检查 Cloudflare 验证
        await self._handle_cloudflare()
        
        # 检查年龄验证
        await self._handle_age_verification()
        
        # 检查 safeid 验证
        await self._handle_safeid()
    
    async def _handle_cloudflare(self):
        """处理 Cloudflare 验证"""
        try:
            # 检查 Cloudflare 验证页面
            if self._is_cloudflare_challenge():
                logger.info("检测到 Cloudflare 验证，等待中...")
                
                # 等待验证完成
                max_wait = 60
                start_time = time.time()
                
                while self._is_cloudflare_challenge():
                    if time.time() - start_time > max_wait:
                        logger.warning("Cloudflare 验证超时")
                        break
                    await asyncio.sleep(1)
                
                # 额外等待页面稳定
                await asyncio.sleep(2)
                
                self._cf_check_count += 1
                logger.info(f"Cloudflare 验证完成 (第 {self._cf_check_count} 次)")
                
                # 如果频繁遇到验证，考虑使用代理
                if self._cf_check_count >= 3:
                    logger.warning("频繁遇到 Cloudflare 验证，建议使用代理")
        except Exception as e:
            logger.debug(f"Cloudflare 检查跳过: {e}")
    
    def _is_cloudflare_challenge(self) -> bool:
        """检查是否是 Cloudflare 验证页面"""
        try:
            # 检查 URL 是否包含 challenge
            if 'challenge' in self.driver.current_url.lower():
                return True
            
            # 检查页面 title
            title = self.driver.title.lower()
            if 'cloudflare' in title or 'checking your browser' in title:
                return True
            
            # 检查页面内容
            page_source = self.driver.page_source.lower()
            if 'cloudflare' in page_source and 'ray id' in page_source:
                return True
            
            return False
        except:
            return False
    
    async def _handle_age_verification(self):
        """处理年龄验证"""
        try:
            current_url = self.driver.current_url
            
            if AGE_VERIFY_URL in current_url or 'ageverify' in current_url.lower():
                logger.info("检测到年龄验证页面，自动通过...")
                
                # 尝试点击"确定"按钮
                try:
                    from selenium.webdriver.common.by import By
                    from selenium.webdriver.support.ui import WebDriverWait
                    from selenium.webdriver.support import expected_conditions as EC
                    
                    # 尝试多种选择器
                    selectors = [
                        "button[type='submit']",
                        "input[type='submit']",
                        ".btn-primary",
                        ".age-yes",
                        "//button[contains(text(), '确定')]",
                        "//button[contains(text(), '确定')]",
                    ]
                    
                    for selector in selectors:
                        try:
                            if selector.startswith('//'):
                                element = WebDriverWait(self.driver, 5).until(
                                    EC.element_to_be_clickable((By.XPATH, selector))
                                )
                            else:
                                element = WebDriverWait(self.driver, 5).until(
                                    EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                                )
                            element.click()
                            logger.info("年龄验证已通过")
                            await asyncio.sleep(2)
                            return
                        except:
                            continue
                    
                    # 如果找不到按钮，尝试提交表单
                    try:
                        self.driver.execute_script("document.querySelector('form').submit()")
                    except:
                        pass
                        
                except Exception as e:
                    logger.warning(f"自动点击年龄验证按钮失败: {e}")
                    
        except Exception as e:
            logger.debug(f"年龄验证检查跳过: {e}")
    
    async def _handle_safeid(self):
        """处理 safeid 验证"""
        try:
            page_source = self.driver.page_source
            
            # 检查是否存在 safeid
            safeid_match = re.search(r"var safeid\s*=\s*['\"]([^'\"]+)['\"]", page_source)
            if safeid_match:
                safeid = safeid_match.group(1)
                logger.info(f"检测到 safeid: {safeid[:10]}...")
                
                # 添加 _safe cookie
                self.driver.add_cookie({
                    'name': '_safe',
                    'value': safeid,
                    'path': '/',
                    'domain': '.sehuatang.org'
                })
                
                # 刷新页面
                self.driver.refresh()
                await asyncio.sleep(2)
                
        except Exception as e:
            logger.debug(f"safeid 检查跳过: {e}")
    
    async def get_page_source(self) -> str:
        """获取页面源码"""
        try:
            if not self.driver:
                return ""
            return self.driver.page_source
        except Exception as e:
            logger.error(f"获取页面源码失败: {e}")
            return ""
    
    async def get_cookies(self) -> List[Dict[str, Any]]:
        """
        获取当前会话的所有 Cookie
        
        Returns:
            Cookie 列表
        """
        try:
            if not self.driver:
                return []
            return self.driver.get_cookies()
        except Exception as e:
            logger.error(f"获取 Cookie 失败: {e}")
            return []
    
    async def get_cookie_string(self) -> str:
        """
        获取 Cookie 字符串
        
        Returns:
            Cookie 字符串，格式为 "key1=value1; key2=value2"
        """
        cookies = await self.get_cookies()
        return "; ".join([f"{c['name']}={c['value']}" for c in cookies])
    
    async def add_cookie(self, cookie_dict: Dict[str, str]):
        """
        添加 Cookie
        
        Args:
            cookie_dict: Cookie 字典，包含 name, value, path, domain
        """
        try:
            if self.driver:
                self.driver.add_cookie(cookie_dict)
                logger.debug(f"已添加 Cookie: {cookie_dict.get('name')}")
        except Exception as e:
            logger.warning(f"添加 Cookie 失败: {e}")
    
    async def _load_cookies(self):
        """从浏览器加载已保存的 Cookie"""
        try:
            if not self.driver or not self.cookie_file.exists():
                return
            
            import json
            with open(self.cookie_file, 'r', encoding='utf-8') as f:
                cookies = json.load(f)
            
            for cookie in cookies:
                try:
                    self.driver.add_cookie(cookie)
                except Exception as e:
                    logger.debug(f"加载单个 Cookie 失败: {e}")
            
            logger.info(f"已加载 {len(cookies)} 个 Cookie")
            
        except Exception as e:
            logger.debug(f"加载 Cookie 失败: {e}")
    
    async def _save_cookies(self):
        """保存 Cookie 到文件"""
        try:
            cookies = await self.get_cookies()
            
            if cookies:
                import json
                with open(self.cookie_file, 'w', encoding='utf-8') as f:
                    json.dump(cookies, f, ensure_ascii=False, indent=2)
                
                logger.info(f"已保存 {len(cookies)} 个 Cookie")
                
        except Exception as e:
            logger.error(f"保存 Cookie 失败: {e}")
    
    async def close(self):
        """关闭浏览器"""
        try:
            # 先保存 Cookie
            await self._save_cookies()
            
            if self.driver:
                self.driver.quit()
                self.driver = None
            
            self._is_running = False
            logger.info("浏览器已关闭")
            
        except Exception as e:
            logger.error(f"关闭浏览器失败: {e}")
    
    @property
    def is_running(self) -> bool:
        """检查浏览器是否运行中"""
        return self._is_running and self.driver is not None
    
    def run_with_driver(self, func):
        """
        在 driver 上下文中执行函数
        
        Args:
            func: 要执行的函数，接收 driver 作为参数
        """
        if self.driver:
            return func(self.driver)
        return None


class SeleniumHttpClient:
    """
    Selenium HTTP 客户端
    
    使用 Selenium 浏览器获取页面内容，兼容 httpx.Response 接口
    """
    
    def __init__(self, browser: SeleniumBrowser = None):
        self.browser = browser or SeleniumBrowser()
        self._html_cache: Dict[str, str] = {}
        self._cache_ttl = 60  # 缓存有效期（秒）
        self._cache_times: Dict[str, float] = {}
    
    async def get(self, url: str, use_cache: bool = True) -> 'SeleniumResponse':
        """
        获取页面内容
        
        Args:
            url: 目标 URL
            use_cache: 是否使用缓存
            
        Returns:
            SeleniumResponse 对象
        """
        async with self.browser._lock:
            # 检查缓存
            if use_cache and url in self._html_cache:
                cached_time = self._cache_times.get(url, 0)
                if time.time() - cached_time < self._cache_ttl:
                    logger.debug(f"使用缓存: {url}")
                    return SeleniumResponse(self._html_cache[url], url)
            
            # 导航到页面
            success = await self.browser.goto(url)
            
            if not success:
                return SeleniumResponse("", url, status_code=500)
            
            # 获取页面源码
            html = await self.browser.get_page_source()
            
            # 更新缓存
            if use_cache:
                self._html_cache[url] = html
                self._cache_times[url] = time.time()
            
            return SeleniumResponse(html, url)
    
    async def get_cookies(self) -> List[Dict[str, Any]]:
        """获取当前浏览器 Cookie"""
        async with self.browser._lock:
            return await self.browser.get_cookies()
    
    async def close(self):
        """关闭客户端"""
        self._html_cache.clear()
        self._cache_times.clear()
    
    def clear_cache(self):
        """清除缓存"""
        self._html_cache.clear()
        self._cache_times.clear()


class SeleniumResponse:
    """
    Selenium 响应对象
    
    模拟 httpx.Response 接口，方便替换
    """
    
    def __init__(self, html: str, url: str = "", status_code: int = 200):
        self._html = html
        self.url = url
        self.status_code = status_code
    
    @property
    def text(self) -> str:
        """返回页面源码"""
        return self._html
    
    @property
    def content(self) -> bytes:
        """返回字节内容"""
        return self._html.encode('utf-8')
    
    def json(self):
        """尝试解析 JSON"""
        import json
        return json.loads(self._html)


# 全局浏览器实例
_browser_instance: Optional[SeleniumBrowser] = None


async def get_browser() -> SeleniumBrowser:
    """获取全局浏览器实例"""
    global _browser_instance
    if _browser_instance is None:
        _browser_instance = SeleniumBrowser()
    return _browser_instance


async def close_browser():
    """关闭全局浏览器"""
    global _browser_instance
    if _browser_instance:
        await _browser_instance.close()
        _browser_instance = None
