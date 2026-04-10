#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
签到专用日志记录器
"""

import logging
from datetime import datetime
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


class CheckinLogger:
    """签到专用日志记录器"""

    def __init__(self):
        self.logger = logging.getLogger("checkin")

    def log_scheduled_start(self, trigger_type: str = "scheduled"):
        """记录定时签到开始"""
        message = f"定时签到任务开始执行 (触发方式: {trigger_type})"
        self.logger.info(message)
        self._save_to_db("INFO", message, "scheduled_checkin_start")

    def log_scheduled_success(self, result: Dict[str, Any]):
        """记录定时签到成功"""
        data = result.get('data', {})
        reply_count = data.get('reply_count', 0)
        execution_time = data.get('execution_time', 0)
        actual_gains = data.get('actual_gains', {})
        already_signed = data.get('already_signed', False)

        if already_signed:
            message = f"定时签到任务完成: 今天已经签到过了，跳过执行"
        else:
            message = (f"定时签到任务完成: 回复 {reply_count} 个帖子, "
                      f"获得积分+{actual_gains.get('points', 0)}, "
                      f"金钱+{actual_gains.get('money', 0)}, "
                      f"执行时间 {execution_time}秒")

        self.logger.info(message)
        self._save_to_db("INFO", message, "scheduled_checkin_success", {
            'reply_count': reply_count,
            'execution_time': execution_time,
            'actual_gains': actual_gains,
            'already_signed': already_signed
        })

    def log_scheduled_failure(self, error: str, execution_time: Optional[int] = None):
        """记录定时签到失败"""
        message = f"定时签到任务失败: {error}"
        if execution_time:
            message += f" (执行时间: {execution_time}秒)"

        self.logger.error(message)
        self._save_to_db("ERROR", message, "scheduled_checkin_failure", {
            'error': error,
            'execution_time': execution_time
        })

    def log_notification_sent(self, notification_type: str, success: bool, error: Optional[str] = None):
        """记录通知发送状态"""
        if success:
            message = f"{notification_type}通知发送成功"
            level = "INFO"
        else:
            message = f"{notification_type}通知发送失败: {error}"
            level = "WARNING"

        self.logger.log(logging.INFO if success else logging.WARNING, message)
        self._save_to_db(level, message, "checkin_notification", {
            'notification_type': notification_type,
            'success': success,
            'error': error
        })

    def log_manual_checkin(self, success: bool, result: Dict[str, Any]):
        """记录手动签到"""
        if success:
            data = result.get('data', {})
            reply_count = data.get('reply_count', 0)
            actual_gains = data.get('actual_gains', {})
            message = (f"手动签到完成: 回复 {reply_count} 个帖子, "
                      f"获得积分+{actual_gains.get('points', 0)}, "
                      f"金钱+{actual_gains.get('money', 0)}")
        else:
            message = f"手动签到失败: {result.get('message', '未知错误')}"

        level = "INFO" if success else "ERROR"
        self.logger.log(logging.INFO if success else logging.ERROR, message)
        self._save_to_db(level, message, "manual_checkin", result)

    def log_test_checkin(self, result: Dict[str, Any]):
        """记录测试签到"""
        data = result.get('data', {})
        reply_count = data.get('reply_count', 0)
        execution_time = data.get('execution_time', 0)

        message = f"模拟签到测试完成: 识别到 {reply_count} 个帖子, 执行时间 {execution_time}秒"
        self.logger.info(message)
        self._save_to_db("INFO", message, "test_checkin", result)

    def log_auto_checkin_toggle(self, enabled: bool, user_action: bool = True):
        """记录自动签到开关状态变化"""
        action_source = "用户操作" if user_action else "系统自动"
        if enabled:
            message = f"自动签到已启用 (触发方式: {action_source})"
            level = "INFO"
        else:
            message = f"自动签到已禁用 (触发方式: {action_source})"
            level = "WARNING"

        self.logger.log(logging.INFO if enabled else logging.WARNING, message)
        self._save_to_db(level, message, "auto_checkin_toggle", {
            'enabled': enabled,
            'user_action': user_action,
            'action_source': action_source
        })

    def _save_to_db(self, level: str, message: str, operation: str, details: Optional[Dict[str, Any]] = None):
        """保存日志到数据库"""
        try:
            import json
            from core.database import SessionLocal
            from models.system_log import SystemLog

            db = SessionLocal()
            try:
                full_message = message
                if operation:
                    full_message = f"[{operation}] {message}"
                if details:
                    full_message += f" | 详情: {json.dumps(details, ensure_ascii=False)}"

                log_entry = SystemLog(
                    level=level,
                    source="checkin_system",
                    message=full_message,
                    operation=operation,
                    details=json.dumps(details, ensure_ascii=False) if details else None
                )
                db.add(log_entry)
                db.commit()
            finally:
                db.close()
        except Exception as e:
            # 数据库日志失败不应该影响主流程
            logger.warning(f"保存签到日志到数据库失败: {e}")


# 全局实例
checkin_logger = CheckinLogger()
