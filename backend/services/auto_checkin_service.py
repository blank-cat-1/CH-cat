#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
自动签到服务
"""

import asyncio
import json
import logging
import random
import re
import time
from datetime import datetime, date, timedelta
from typing import List, Dict, Optional, Tuple
from urllib.parse import urljoin

from sqlalchemy.orm import Session

from core.database import SessionLocal
from models.checkin import CheckInRecord, CheckInConfig
from services.crawler.http_client import HttpClient

logger = logging.getLogger(__name__)


class AutoCheckinService:
    """自动签到服务"""

    def __init__(self):
        self.base_url = "https://sehuatang.org/"
        self.checkin_url = "https://sehuatang.org/plugin.php?id=dd_sign:index"

        # 针对板块的随机回复模板
        self.reply_templates = {
            'resource_quality': [
                "画质很清晰，感谢分享",
                "这个质量确实不错",
                "高清资源，必须支持",
                "画面效果很棒",
                "清晰度很满意",
                "这个分辨率刚好",
                "码率控制得不错",
                "压制质量很好",
            ],
            'technical_specs': [
                "115链接收到，谢谢分享",
                "ED2K链接很全，感谢整理",
                "磁力链接收藏了",
                "下载速度很快，好资源",
                "链接有效，已下载",
                "文件完整，感谢楼主",
                "下载链接很稳定",
            ],
            'content_appreciation': [
                "这个系列质量都不错",
                "演技和颜值都在在线",
                "这个角色很有特色",
                "剧情设定不错",
                "这种类型的比较少见",
                "故事背景很吸引人",
                "这个题材很有意思",
            ],
            'classic_content': [
                "经典作品，值得收藏",
                "这个系列确实不错",
                "老牌经典，还是有感觉的",
                "怀念这种风格的",
                "经典重温，还是很有感觉",
                "经典不过时",
                "这种经典百看不厌",
            ],
            'collection_support': [
                "收藏了，慢慢欣赏",
                "先收藏了，晚上看",
                "好东西，必须收藏",
                "加入收藏夹了",
                "收藏备用，谢谢",
                "先存起来，感谢分享",
            ],
            'general_thanks': [
                "楼主辛苦了，感谢分享",
                "谢谢楼主的无私分享",
                "楼主人品爆棚",
                "好人一生平安",
                "楼主威武，继续加油",
                "楼主太给力了",
                "感谢楼主的贡献",
            ]
        }

    async def perform_daily_checkin(self, test_mode: bool = False) -> Dict[str, any]:
        """执行每日签到"""
        if test_mode:
            logger.info("🧪 开始执行签到测试模式（不实际提交）")
        else:
            logger.info("🎯 开始执行每日签到任务")

        db = SessionLocal()
        start_time = datetime.now()
        before_stats = None

        try:
            today = date.today()

            # 获取签到配置
            config = db.query(CheckInConfig).first()
            if not config:
                config = CheckInConfig()
                db.add(config)
                db.commit()

            if not config.enabled:
                logger.info("🔕 自动签到功能已禁用")
                return {'success': False, 'message': '自动签到功能已禁用'}

            # 检查今天是否已经签到
            existing_checkin = None
            if not test_mode:
                existing_checkin = db.query(CheckInRecord).filter(
                    CheckInRecord.checkin_date == today,
                    CheckInRecord.status == 'success'
                ).first()

                if existing_checkin:
                    logger.info("✅ 今天已经签到过了，跳过签到流程")
                    return {
                        'success': True,
                        'message': '今天已经签到过了',
                        'data': {'reply_count': 0, 'already_signed': True}
                    }

            # 获取 Cookie
            http_client_temp = HttpClient(max_concurrent=1, timeout=30)
            await http_client_temp.create()
            cookies_dict = await http_client_temp._get_cookies()
            await http_client_temp.close()

            if not cookies_dict:
                raise Exception("未找到有效的Cookie")

            cookie_str = "; ".join([f"{k}={v}" for k, v in cookies_dict.items()])

            # 步骤1: 获取签到前用户状态
            if not test_mode:
                try:
                    from services.user_profile_parser import user_profile_parser
                    before_stats = await user_profile_parser.get_user_profile_stats(cookie_str)
                    if before_stats:
                        logger.info(f"签到前状态: 积分={before_stats.points}, 金钱={before_stats.money}, 色币={before_stats.coins}")
                except Exception as e:
                    logger.warning(f"获取签到前状态失败: {e}")
                    before_stats = None

            # 步骤2: 执行回复任务
            if existing_checkin:
                reply_result = {'success': True, 'reply_count': 0, 'post_ids': [], 'message': '已签到，跳过回复任务'}
                logger.info("✅ 已签到，跳过回复任务")
            else:
                reply_result = await self._perform_random_replies(config, db, test_mode)

            # 步骤3: 执行签到
            if not test_mode:
                signin_result = await self._perform_signin()
            else:
                signin_result = {'success': True, 'points': 0, 'message': '测试模式：跳过实际签到'}

            # 步骤4: 获取签到后用户状态
            after_stats = None
            if not test_mode and signin_result.get('success'):
                logger.info("📊 获取签到后用户状态...")
                try:
                    await asyncio.sleep(3)
                    from services.user_profile_parser import user_profile_parser
                    after_stats = await user_profile_parser.get_user_profile_stats(cookie_str)
                    if after_stats:
                        logger.info(f"签到后状态: 积分={after_stats.points}, 金钱={after_stats.money}, 色币={after_stats.coins}")
                except Exception as e:
                    logger.warning(f"获取签到后状态失败: {e}")
                    after_stats = None

            # 步骤5: 计算实际收益
            actual_points_gained = 0
            actual_money_gained = 0
            actual_coins_gained = 0

            if before_stats and after_stats:
                actual_points_gained = after_stats.points - before_stats.points
                actual_money_gained = after_stats.money - before_stats.money
                actual_coins_gained = after_stats.coins - before_stats.coins
                logger.info(f"💰 实际收益: 积分+{actual_points_gained}, 金钱+{actual_money_gained}, 色币+{actual_coins_gained}")

            # 步骤6: 创建签到记录
            execution_time = int((datetime.now() - start_time).total_seconds())

            if test_mode:
                status = 'test_success'
                reward_description = '测试模式：跳过实际签到'
            else:
                if signin_result.get('success', False):
                    status = 'success'
                    reward_description = signin_result.get('message', '')
                else:
                    status = 'failed'
                    reward_description = signin_result.get('message', '签到失败')

            checkin_record = CheckInRecord(
                checkin_date=today,
                status=status,
                reply_count=reply_result.get('reply_count', 0),
                points_before=before_stats.points if before_stats else 0,
                money_before=before_stats.money if before_stats else 0,
                coins_before=before_stats.coins if before_stats else 0,
                points_after=after_stats.points if after_stats else 0,
                money_after=after_stats.money if after_stats else 0,
                coins_after=after_stats.coins if after_stats else 0,
                actual_points_gained=actual_points_gained,
                actual_money_gained=actual_money_gained,
                actual_coins_gained=actual_coins_gained,
                reward_points=signin_result.get('reward_amount', 0) or signin_result.get('points', 0),
                reward_description=reward_description,
                execution_time=execution_time,
                replied_posts=json.dumps(reply_result.get('post_ids', [])),
                error_message=reward_description if status == 'failed' else None
            )
            db.add(checkin_record)
            db.commit()

            if test_mode:
                logger.info(f"🧪 测试完成！模拟回复 {reply_result.get('reply_count', 0)} 个帖子")
            else:
                logger.info(f"✅ 签到完成！回复 {reply_result.get('reply_count', 0)} 个帖子，实际获得: 积分+{actual_points_gained}, 金钱+{actual_money_gained}")

            return {
                'success': True,
                'message': '签到完成',
                'data': {
                    'reply_count': reply_result.get('reply_count', 0),
                    'execution_time': execution_time,
                    'actual_gains': {
                        'points': actual_points_gained,
                        'money': actual_money_gained,
                        'coins': actual_coins_gained
                    },
                    'before_stats': {
                        'points': before_stats.points if before_stats else 0,
                        'money': before_stats.money if before_stats else 0,
                        'coins': before_stats.coins if before_stats else 0
                    } if before_stats else None,
                    'after_stats': {
                        'points': after_stats.points if after_stats else 0,
                        'money': after_stats.money if after_stats else 0,
                        'coins': after_stats.coins if after_stats else 0
                    } if after_stats else None
                }
            }

        except Exception as e:
            logger.error(f"❌ 签到过程出错: {e}")
            try:
                execution_time = int((datetime.now() - start_time).total_seconds())
                status = 'test_failed' if test_mode else 'failed'
                error_message = f'测试失败: {str(e)}' if test_mode else str(e)

                checkin_record = CheckInRecord(
                    checkin_date=date.today(),
                    status=status,
                    error_message=error_message,
                    execution_time=execution_time
                )
                db.add(checkin_record)
                db.commit()
            except Exception as db_error:
                logger.error(f"保存失败记录时出错: {db_error}")

            return {'success': False, 'message': f'签到失败: {str(e)}'}

        finally:
            db.close()

    async def _perform_random_replies(self, config: CheckInConfig, db: Session, test_mode: bool = False) -> Dict[str, any]:
        """执行随机回复"""
        if test_mode:
            logger.info("=" * 60)
            logger.info("🧪 【签到模拟测试开始】")
            logger.info(f"🎯 目标回复数量: {config.reply_count_per_day} 个帖子")
            logger.info(f"🎲 随机页码范围: 1-50")
            logger.info(f"📋 目标板块: {config.target_board}")
            logger.info("⚠️  注意：这是模拟测试，不会实际提交回复")
            logger.info("=" * 60)
        else:
            logger.info(f"📝 开始随机回复，目标数量: {config.reply_count_per_day}")

        http_client = HttpClient(max_concurrent=1, timeout=30)
        await http_client.create()

        try:
            replied_posts = []
            reply_count = 0
            attempt = 0
            max_attempts = config.reply_count_per_day * 3

            while reply_count < config.reply_count_per_day and attempt < max_attempts:
                attempt += 1
                try:
                    random_page = random.randint(1, 50)
                    posts = await self._get_random_posts(http_client, config.target_board, random_page)

                    if not posts:
                        continue

                    available_posts = [p for p in posts if p['tid'] not in replied_posts]
                    if not available_posts:
                        continue

                    post = random.choice(available_posts)
                    reply_content = self._generate_random_reply()

                    if test_mode:
                        logger.info(f"🧪 [模拟] 第{reply_count + 1}个帖子: {post['title'][:30]}... 回复: {reply_content}")
                        await asyncio.sleep(random.randint(1, 3))
                        reply_success = True
                    else:
                        reply_success = await self._post_reply(http_client, post['tid'], reply_content)

                    if reply_success:
                        replied_posts.append(post['tid'])
                        reply_count += 1
                        logger.info(f"✅ 回复成功: {post['title'][:30]}... 回复内容: {reply_content}")
                        delay = random.randint(10, 60)
                        await asyncio.sleep(delay)
                    else:
                        logger.warning(f"❌ 回复失败: {post['title'][:30]}...")

                except Exception as e:
                    logger.error(f"回复过程出错: {e}")
                    continue

            if test_mode:
                logger.info(f"🧪 【签到模拟测试完成】成功识别 {reply_count} 个帖子")

            return {'reply_count': reply_count, 'post_ids': replied_posts}

        finally:
            await http_client.close()

    async def _get_random_posts(self, http_client: HttpClient, board: str, page: int) -> List[Dict]:
        """获取随机帖子列表"""
        try:
            board_url = f"{self.base_url}forum.php?mod=forumdisplay&fid=95&filter=typeid&typeid=716&page={page}"
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Referer': self.base_url
            }

            response = await http_client.get(board_url, headers=headers)
            if response.status_code != 200:
                return []

            return self._parse_post_list(response.text)

        except Exception as e:
            logger.error(f"获取帖子列表失败: {e}")
            return []

    def _parse_post_list(self, html: str) -> List[Dict]:
        """解析帖子列表"""
        try:
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(html, 'html.parser')
            posts = []

            post_links = soup.select('tbody[id^="normalthread_"] a.xst')
            if not post_links:
                post_links = soup.select('a[href*="viewthread"]')
            if not post_links:
                post_links = soup.select('a[href*="thread-"]')

            for link in post_links:
                href = link.get('href')
                title = link.get_text(strip=True)

                if href and title:
                    tid_match = re.search(r'viewthread.*?tid[=&](\d+)', href)
                    if not tid_match:
                        tid_match = re.search(r'thread-(\d+)', href)

                    if tid_match:
                        posts.append({
                            'tid': tid_match.group(1),
                            'title': title,
                            'url': urljoin(self.base_url, href)
                        })

            unique_posts = []
            seen_tids = set()
            for post in posts:
                if post['tid'] not in seen_tids:
                    unique_posts.append(post)
                    seen_tids.add(post['tid'])

            return unique_posts[:20]

        except Exception as e:
            logger.error(f"解析帖子列表失败: {e}")
            return []

    def _generate_random_reply(self) -> str:
        """生成随机回复内容"""
        categories = list(self.reply_templates.keys())
        category = random.choice(categories)
        replies = self.reply_templates[category]
        base_reply = random.choice(replies)

        variations = [
            base_reply,
            f"{base_reply}！",
            f"{base_reply}。",
            f"{base_reply}，支持一下",
            f"支持，{base_reply}",
        ]
        return random.choice(variations)

    async def _post_reply(self, http_client: HttpClient, tid: str, content: str) -> bool:
        """发送回复到指定帖子"""
        try:
            thread_url = f"https://sehuatang.org/forum.php?mod=viewthread&tid={tid}"
            thread_response = await http_client.get(
                thread_url,
                headers={'Referer': 'https://sehuatang.org/forum.php?mod=forumdisplay&fid=95'}
            )

            if thread_response.status_code != 200:
                return False

            from bs4 import BeautifulSoup
            soup = BeautifulSoup(thread_response.text, 'html.parser')
            formhash_input = soup.find('input', {'name': 'formhash'})
            formhash = formhash_input['value'] if formhash_input else None

            if not formhash:
                onclick_scripts = soup.find_all(string=re.compile(r"fastpostvalidate.*'formhash':\s*'(\w+)'"))
                if onclick_scripts:
                    match = re.search(r"'formhash':\s*'(\w+)'", onclick_scripts[0])
                    if match:
                        formhash = match.group(1)

            if not formhash:
                return False

            reply_url = f"https://sehuatang.org/forum.php?mod=post&action=reply&fid=95&tid={tid}&extra=page%3D1&replysubmit=yes&infloat=yes&handlekey=fastpost&inajax=1"
            reply_data = {
                'message': content,
                'posttime': int(time.time()),
                'formhash': formhash,
                'usesig': '1',
                'subject': '',
            }

            response = await http_client.post(
                reply_url,
                data=reply_data,
                headers={
                    'Referer': thread_url,
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                }
            )

            if response.status_code == 200:
                response_text = response.text
                processed_text = self._preprocess_xml_text(response_text)

                if '回复发布成功' in processed_text or '操作成功' in processed_text:
                    return True
                elif '审核' in processed_text:
                    return True
                elif '需要先登录' in processed_text:
                    return False
                else:
                    return False

            return False

        except Exception as e:
            logger.error(f"发送回复时出错: {e}")
            return False

    def _preprocess_xml_text(self, text: str) -> str:
        """处理 Discuz 返回的 XML CDATA"""
        if not text or not isinstance(text, str):
            return str(text) if text else ""

        if '签到成功' in text:
            success_match = re.search(r'签到成功[^\'"]*', text)
            if success_match:
                return success_match.group(0)

        if '回复发布成功' in text:
            return '回复发布成功'

        if '<![CDATA[' not in text:
            cleaned = re.sub(r'<[^>]+>', ' ', text)
            cleaned = re.sub(r'\s+', ' ', cleaned).strip()
            return cleaned

        try:
            import xml.etree.ElementTree as ET
            from bs4 import BeautifulSoup

            root = ET.fromstring(text)
            cdata = root.text
            if not cdata:
                return text

            soup = BeautifulSoup(cdata, 'html.parser')
            for script in soup.find_all(['script', 'style']):
                script.decompose()
            text_content = soup.get_text(separator=' ', strip=True)

            if '签到成功' in text_content:
                success_match = re.search(r'签到成功[^\'"]*', text_content)
                if success_match:
                    return success_match.group(0)
            if '回复发布成功' in text_content:
                return '回复发布成功'

            cleaned = re.sub(r'\s+', ' ', text_content).strip()
            return cleaned or "操作已完成"

        except Exception as e:
            match = re.search(r'CDATA\[(.*?)\]\]>', text, re.DOTALL)
            if match:
                content = match.group(1).strip()
                content = re.sub(r'<script.*?</script>', '', content, flags=re.DOTALL)
                content = re.sub(r'<[^>]+>', ' ', content)
                if '回复发布成功' in content:
                    return '回复发布成功'
                return re.sub(r'\s+', ' ', content).strip() or "操作已完成"

            cleaned = re.sub(r'<[^>]+>', ' ', text)
            cleaned = re.sub(r'\s+', ' ', cleaned).strip()
            return cleaned or "操作已完成"

    async def _perform_signin(self) -> Dict[str, any]:
        """执行签到"""
        try:
            logger.info("🎯 开始执行签到")

            http_client = HttpClient(max_concurrent=1, timeout=30)
            await http_client.create()

            try:
                base_url = "https://sehuatang.org"

                # 1. 访问签到页面获取基础信息
                sign_plugin_url = f'{base_url}/plugin.php?id=dd_sign&mod=sign'
                try:
                    await http_client.get(sign_plugin_url, headers={'Referer': f'{base_url}/'})
                except Exception as e:
                    logger.warning(f"访问初始签到页面失败: {e}，继续...")

                # 2. 获取签到表单参数
                ajax_url = f'{base_url}/plugin.php?id=dd_sign&ac=sign&infloat=yes&handlekey=pc_click_ddsign&inajax=1&ajaxtarget=fwin_content_pc_click_ddsign'
                response = await http_client.get(ajax_url, headers={'Referer': sign_plugin_url})

                if response.status_code != 200:
                    raise Exception(f"获取签到表单失败，状态码: {response.status_code}")

                raw_xml = response.text

                if "系统繁忙" in raw_xml:
                    raise Exception("系统繁忙，请稍后再试")

                from bs4 import BeautifulSoup
                soup = BeautifulSoup(raw_xml, 'xml')
                html_content = soup.find('root').string if soup.find('root') else None

                if not html_content:
                    processed_text = self._preprocess_xml_text(raw_xml)
                    if '已经签到' in processed_text:
                        return {"success": True, "message": processed_text, "status": "已签到"}
                    else:
                        raise Exception(f"无法从Ajax响应中提取HTML内容: {processed_text}")

                # 解析HTML内容获取表单参数
                root = BeautifulSoup(html_content, 'html.parser')
                formhash_input = root.find('input', {'name': 'formhash'})
                signtoken_input = root.find('input', {'name': 'signtoken'})
                action_form = root.find('form', {'name': 'login'})
                secqaa_span = root.find('span', id=re.compile(r'^secqaa_'))

                if not all([formhash_input, signtoken_input, action_form, secqaa_span]):
                    processed_text = self._preprocess_xml_text(raw_xml)
                    if '已经签到' in processed_text:
                        return {"success": True, "message": processed_text, "status": "已签到"}
                    missing = []
                    if not formhash_input: missing.append("formhash")
                    if not signtoken_input: missing.append("signtoken")
                    if not action_form: missing.append("form action")
                    if not secqaa_span: missing.append("验证码ID")
                    raise Exception(f"未能从签到表单中提取必要参数: {', '.join(missing)}")

                formhash = formhash_input['value']
                signtoken = signtoken_input['value']
                action_path = action_form['action'].lstrip('/')
                action_url = f"{base_url}/{action_path}"
                id_hash = secqaa_span['id'].removeprefix('secqaa_')

                # 3. 获取验证问题
                qaa_url = f'{base_url}/misc.php?mod=secqaa&action=update&idhash={id_hash}&{random.random()}'
                qaa_response = await http_client.get(qaa_url, headers={'Referer': sign_plugin_url})
                qes_rsl = re.findall(r"'(.*?) = \?'", qaa_response.text, re.MULTILINE | re.IGNORECASE)

                if not qes_rsl or not qes_rsl[0]:
                    raise Exception(f'未能获取到有效的验证问题。响应: {qaa_response.text[:200]}')

                qes = qes_rsl[0]
                try:
                    ans = eval(qes, {"__builtins__": {}}, {})
                    if not isinstance(ans, int):
                        raise ValueError("计算结果不是整数")
                except Exception as eval_e:
                    raise Exception(f'计算验证问题 "{qes}" 时出错: {eval_e}')

                logger.info(f'获取并计算验证问题成功: {qes} = {ans}')

                # 4. 提交签到
                submit_url = f'{action_url}&inajax=1'
                submit_data = {
                    'formhash': formhash,
                    'signtoken': signtoken,
                    'secqaahash': id_hash,
                    'secanswer': ans
                }

                submit_response = await http_client.post(
                    submit_url,
                    data=submit_data,
                    headers={'Referer': sign_plugin_url}
                )

                if submit_response.status_code != 200:
                    raise Exception(f"提交签到失败，状态码: {submit_response.status_code}")

                response_text = submit_response.text
                processed_text = self._preprocess_xml_text(response_text)
                logger.info(f"签到结果: {processed_text}")

                if '签到成功' in processed_text:
                    reward_match = re.search(r'(?:获得|奖励)\s*(\d+)\s*金钱', processed_text)
                    reward_amount = int(reward_match.group(1)) if reward_match else None
                    success_msg = re.search(r"(签到成功.+)", processed_text)
                    message = success_msg.group(1).strip() if success_msg else processed_text
                    logger.info(f"✅ 签到成功: {message}")
                    return {"success": True, "message": message, "status": "签到成功", "reward_amount": reward_amount}

                elif '已签到' in processed_text:
                    message = re.search(r"(已经签到.+)", processed_text)
                    message = message.group(1).strip() if message else processed_text
                    logger.info(f"ℹ️ 已签到: {message}")
                    return {"success": True, "message": message, "status": "已签到"}

                elif '需要先登录' in processed_text:
                    raise Exception("Cookie无效或已过期")
                else:
                    raise Exception(f"签到失败: {processed_text}")

            finally:
                await http_client.close()

        except Exception as e:
            logger.error(f"签到失败: {e}")
            return {"success": False, "message": str(e)}

    async def get_checkin_stats(self, days: int = 30) -> Dict[str, any]:
        """获取签到统计"""
        db = SessionLocal()
        try:
            start_date = date.today() - timedelta(days=days)

            records = db.query(CheckInRecord).filter(
                CheckInRecord.checkin_date >= start_date
            ).order_by(CheckInRecord.checkin_date.desc()).all()

            total_days = len(records)
            success_days = len([r for r in records if r.status == 'success'])
            total_replies = sum(r.reply_count or 0 for r in records)

            total_actual_points = sum(r.actual_points_gained or 0 for r in records)
            total_actual_money = sum(r.actual_money_gained or 0 for r in records)
            total_actual_coins = sum(r.actual_coins_gained or 0 for r in records)

            if total_actual_points == 0:
                total_actual_points = sum(r.reward_points or 0 for r in records)

            # 连续签到天数
            consecutive_days = 0
            current_date = date.today()
            for record in records:
                if record.checkin_date == current_date and record.status == 'success':
                    consecutive_days += 1
                    current_date -= timedelta(days=1)
                else:
                    break

            # 获取最后签到时间
            last_checkin = None
            if records:
                last_successful_record = next((r for r in records if r.status == 'success'), None)
                if last_successful_record:
                    last_checkin = last_successful_record.checkin_date.isoformat()

            # 今日收益
            today_record = next((r for r in records if r.checkin_date == date.today()), None)
            today_gains = {
                'points': today_record.actual_points_gained or 0 if today_record else 0,
                'money': today_record.actual_money_gained or 0 if today_record else 0,
                'coins': today_record.actual_coins_gained or 0 if today_record else 0
            }

            # 本周收益
            week_start = date.today() - timedelta(days=6)
            week_records = [r for r in records if r.checkin_date >= week_start]
            week_gains = {
                'points': sum(r.actual_points_gained or 0 for r in week_records),
                'money': sum(r.actual_money_gained or 0 for r in week_records),
                'coins': sum(r.actual_coins_gained or 0 for r in week_records)
            }

            # 本月收益
            month_start = date.today().replace(day=1)
            month_records = [r for r in records if r.checkin_date >= month_start]
            month_gains = {
                'points': sum(r.actual_points_gained or 0 for r in month_records),
                'money': sum(r.actual_money_gained or 0 for r in month_records),
                'coins': sum(r.actual_coins_gained or 0 for r in month_records)
            }

            return {
                'total_checkins': total_days,
                'current_streak': consecutive_days,
                'total_replies': total_replies,
                'last_checkin': last_checkin,
                'total_actual_points': total_actual_points,
                'total_actual_money': total_actual_money,
                'total_actual_coins': total_actual_coins,
                'today_gains': today_gains,
                'week_gains': week_gains,
                'month_gains': month_gains,
                'avg_points_per_day': round(total_actual_points / max(success_days, 1), 1),
                'avg_money_per_day': round(total_actual_money / max(success_days, 1), 1),
                'recent_records': [
                    {
                        'date': r.checkin_date.isoformat(),
                        'status': r.status,
                        'reply_count': r.reply_count or 0,
                        'actual_gains': {
                            'points': r.actual_points_gained or 0,
                            'money': r.actual_money_gained or 0,
                            'coins': r.actual_coins_gained or 0
                        },
                        'message': r.reward_description or '',
                        'execution_time': r.execution_time or 0
                    }
                    for r in records[:10]
                ]
            }

        finally:
            db.close()


# 全局服务实例
auto_checkin_service = AutoCheckinService()
