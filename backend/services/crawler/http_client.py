#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
HTTP客户端 - 支持 Selenium 和 httpx 两种模式
"""

import asyncio
import time
import random
from typing import Optional, Dict, Union
import logging
import os

from .selenium_browser import get_browser, SeleniumHttpClient, SeleniumResponse

logger = logging.getLogger(__name__)


class TokenBucket:
    """令牌桶速率限制"""

    def __init__(self, rate: float = 8.0, burst: int = 12):
        self.rate = rate
        self.burst = burst
        self.tokens = float(burst)
        self.last_refill = time.time()
        self._lock = asyncio.Lock()
        self.original_rate = rate

    async def acquire(self) -> None:
        """获取令牌"""
        async with self._lock:
            now = time.time()
            tokens_to_add = (now - self.last_refill) * self.rate
            self.tokens = min(self.burst, self.tokens + tokens_to_add)
            self.last_refill = now

            if self.tokens >= 1.0:
                self.tokens -= 1.0
                return

            wait_time = (1.0 - self.tokens) / self.rate

        if wait_time > 0:
            await asyncio.sleep(wait_time)
        await self.acquire()

    def adjust_rate(self, factor: float) -> None:
        """调整速率"""
        self.rate = max(0.1, self.rate * factor)
        logger.debug(f"速率调整为: {self.rate:.2f} req/s")


class HttpClient:
    """
    HTTP客户端 - 支持 Selenium 自动维护 Cookie

    优先使用 Selenium 模式，自动处理 Cloudflare/年龄验证，
    无需手动配置 Cookie。
    """

    def __init__(
        self,
        max_concurrent: int = 12,
        timeout: int = 30,
        rate_limit: float = 8.0,
        use_selenium: bool = True
    ):
        self.max_concurrent = max_concurrent
        self.timeout = timeout
        self.rate_limit = rate_limit
        self.use_selenium = use_selenium
        self.semaphore = asyncio.Semaphore(max_concurrent)
        self.token_bucket = TokenBucket(rate=rate_limit)
        self.client: Optional[Union[SeleniumHttpClient, 'httpx.AsyncClient']] = None
        self.browser = None
        self.error_count = 0
        self.last_error_time = 0.0
        self._initialized = False

    async def create(self) -> None:
        """创建HTTP客户端"""
        logger.info(f"创建HTTP客户端 (Selenium模式: {self.use_selenium})")

        if self.use_selenium:
            # Selenium 模式 - 自动维护 Cookie
            self.browser = await get_browser()
            await self.browser.init_browser()
            self.client = SeleniumHttpClient(self.browser)
        else:
            # httpx 模式 - 传统方式
            import httpx
            from .cookies import get_active_cookies

            cookies = get_active_cookies()
            proxies = self._load_proxies()

            timeout = httpx.Timeout(
                connect=10.0,
                read=self.timeout,
                write=10.0,
                pool=30.0
            )

            self.client = httpx.AsyncClient(
                timeout=timeout,
                cookies=self._parse_cookies(cookies) if cookies else None,
                proxies=proxies,
                follow_redirects=True,
                verify=False
            )

        self._initialized = True
        logger.info(f"HTTP客户端创建成功: 模式={'Selenium(自动Cookie)' if self.use_selenium else 'httpx'}")

    async def get(self, url: str, headers: Optional[Dict[str, str]] = None) -> Union[SeleniumResponse, 'httpx.Response']:
        """
        发送GET请求

        Args:
            url: 请求URL
            headers: 额外的请求头 (Selenium模式下会被忽略)

        Returns:
            HTTP响应
        """
        if not self._initialized:
            await self.create()

        async with self.semaphore:
            await self.token_bucket.acquire()
            await self._add_jitter()

            try:
                if self.use_selenium:
                    response = await self.client.get(url)
                    if response.status_code != 200:
                        self._handle_error(Exception(f"HTTP {response.status_code}"))
                    else:
                        self._handle_success()
                    return response
                else:
                    response = await self.client.get(url, headers=headers or {})

                    # 403时尝试FlareSolverr（仅在非Selenium模式下，需要额外部署FlareSolverr服务）
                    if response.status_code == 403:
                        flaresolverr_result = await self._fetch_with_flaresolverr(url)
                        if flaresolverr_result:
                            logger.info("FlareSolverr 备选方案成功")
                            return FlareSolverrResponse(flaresolverr_result)

                    self._handle_success()
                    return response

            except Exception as e:
                self._handle_error(e)
                raise

    async def post(
        self,
        url: str,
        data: Optional[Dict] = None,
        headers: Optional[Dict[str, str]] = None
    ) -> 'httpx.Response':
        """发送POST请求 (仅httpx模式)"""
        if not self._initialized:
            await self.create()

        if self.use_selenium:
            logger.warning("POST请求在Selenium模式下不支持，使用GET")
            return await self.get(url)

        async with self.semaphore:
            await self.token_bucket.acquire()
            await self._add_jitter()

            try:
                response = await self.client.post(url, data=data or {}, headers=headers or {})
                self._handle_success()
                return response
            except Exception as e:
                self._handle_error(e)
                raise

    async def close(self) -> None:
        """关闭客户端"""
        if self.client:
            if self.use_selenium:
                # Selenium 模式下不关闭浏览器，只关闭客户端
                await self.client.close()
            else:
                await self.client.aclose()
            logger.info("HTTP客户端已关闭")
        self._initialized = False

    async def get_browser_cookies(self):
        """获取当前浏览器的所有 Cookie"""
        if self.browser:
            return await self.browser.get_cookies()
        return []

    async def _add_jitter(self) -> None:
        """添加随机抖动"""
        jitter_ms = random.randint(50, 150)
        await asyncio.sleep(jitter_ms / 1000.0)

    async def _fetch_with_flaresolverr(self, url: str) -> Optional[str]:
        """使用FlareSolverr获取页面"""
        try:
            import httpx

            flaresolverr_url = os.environ.get('FLARESOLVERR_URL', 'http://localhost:8191')

            payload = {
                "cmd": "request.get",
                "url": url,
                "maxTimeout": 60000
            }

            async with httpx.AsyncClient(timeout=60) as client:
                response = await client.post(f"{flaresolverr_url}/v1", json=payload)

                if response.status_code == 200:
                    result = response.json()
                    if result.get('status') == 'success':
                        return result['solution']['content']

            return None

        except Exception as e:
            logger.warning(f"FlareSolverr请求失败: {e}")
            return None

    def _load_proxies(self) -> Optional[Dict[str, str]]:
        """加载代理配置"""
        try:
            http_proxy = os.environ.get('HTTP_PROXY') or os.environ.get('http_proxy')
            https_proxy = os.environ.get('HTTPS_PROXY') or os.environ.get('https_proxy')

            if not http_proxy and not https_proxy:
                return None

            proxies = {}
            if http_proxy:
                proxies['http://'] = http_proxy
            if https_proxy:
                proxies['https://'] = https_proxy

            return proxies if proxies else None

        except Exception as e:
            logger.warning(f"加载代理失败: {e}")
            return None

    def _parse_cookies(self, cookie_string: str) -> Optional[Dict[str, str]]:
        """解析Cookie字符串"""
        if not cookie_string:
            return None

        cookies = {}
        for item in cookie_string.split(';'):
            if '=' in item:
                key, value = item.split('=', 1)
                cookies[key.strip()] = value.strip()

        return cookies if cookies else None

    def _handle_error(self, error: Exception) -> None:
        """处理错误"""
        now = time.time()
        self.error_count += 1
        self.last_error_time = now

        if self.error_count >= 5:
            self.token_bucket.adjust_rate(0.5)
            logger.warning(f"错误频繁({self.error_count}次)，降低请求速率")
            self.error_count = 0

    def _handle_success(self) -> None:
        """处理成功"""
        now = time.time()

        if (now - self.last_error_time) > 300:
            if self.token_bucket.rate < self.token_bucket.original_rate:
                self.token_bucket.adjust_rate(1.1)


class FlareSolverrResponse:
    """FlareSolverr响应包装器"""

    def __init__(self, html: str):
        self._html = html
        self.status_code = 200

    @property
    def text(self) -> str:
        return self._html

    @property
    def content(self) -> bytes:
        return self._html.encode('utf-8')
