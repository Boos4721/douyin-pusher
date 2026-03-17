"""
抖音页面元素选择器 - 封装 pinchtab 页面元素选择功能
"""

import json
import subprocess
from typing import Dict, List, Optional


class Selector:
    """页面元素选择器"""

    def __init__(self):
        self._elements: Dict[str, str] = {}
        self._last_snapshot: Optional[dict] = None

    def snap(self) -> Dict:
        """获取页面快照"""
        try:
            result = subprocess.run(
                ["pinchtab", "snap", "-i"],
                capture_output=True,
                text=True,
                timeout=15
            )
            data = json.loads(result.stdout)
            self._last_snapshot = data
            return data
        except Exception as e:
            print(f"页面快照失败: {e}")
            return {"nodes": []}

    def get_elements(self, keywords: Dict[str, List[str]]) -> Dict[str, Optional[str]]:
        """
        根据关键词获取页面元素

        Args:
            keywords: 关键词映射，如 {"upload": ["上传", "选择文件"], "publish": ["发布"]}

        Returns:
            元素 ref 映射
        """
        nodes = self.snap().get("nodes", [])
        elements = {}

        for key, kw_list in keywords.items():
            elements[key] = self._find_element(nodes, kw_list)

        self._elements = elements
        return elements

    def _find_element(self, nodes: List[dict], keywords: List[str]) -> Optional[str]:
        """根据关键词查找元素"""
        for node in nodes:
            name = node.get("name", "")
            for kw in keywords:
                if kw in name:
                    return node.get("ref")
        return None

    def find_by_text(self, text: str) -> Optional[str]:
        """根据文本查找元素"""
        nodes = self.snap().get("nodes", [])
        return self._find_element(nodes, [text])

    def find_all_by_text(self, text: str) -> List[Dict]:
        """查找所有匹配文本的元素"""
        nodes = self.snap().get("nodes", [])
        results = []
        for node in nodes:
            if text in node.get("name", ""):
                results.append({"ref": node.get("ref"), "name": node.get("name")})
        return results

    def click(self, ref: str) -> bool:
        """点击元素"""
        try:
            subprocess.run(
                ["pinchtab", "click", ref],
                capture_output=True,
                text=True,
                timeout=15
            )
            return True
        except Exception as e:
            print(f"点击失败: {e}")
            return False

    def fill(self, ref: str, text: str) -> bool:
        """填写输入框"""
        try:
            subprocess.run(
                ["pinchtab", "fill", ref, text],
                capture_output=True,
                text=True,
                timeout=15
            )
            return True
        except Exception as e:
            print(f"填写失败: {e}")
            return False

    def upload(self, ref: str, file_path: str) -> bool:
        """上传文件"""
        try:
            subprocess.run(
                ["pinchtab", "upload", file_path, "--selector", ref],
                capture_output=True,
                text=True,
                timeout=60
            )
            return True
        except Exception as e:
            print(f"上传失败: {e}")
            return False

    def get_text(self) -> str:
        """获取页面文本"""
        try:
            result = subprocess.run(
                ["pinchtab", "text"],
                capture_output=True,
                text=True,
                timeout=15
            )
            return result.stdout
        except Exception as e:
            print(f"获取文本失败: {e}")
            return ""


# 预定义选择器
class DouyinSelectors:
    """抖音常用页面选择器"""

    @staticmethod
    def upload_page() -> Dict[str, List[str]]:
        """上传页面元素"""
        return {
            "file_input": ["选择文件", "上传视频", "input[type=file]"],
            "title_input": ["标题", "描述", "输入标题"],
            "publish_btn": ["发布", "发布视频", "确认发布"],
            "cover_btn": ["封面", "设置封面"],
            "location_btn": ["位置", "添加位置"],
        }

    @staticmethod
    def home_page() -> Dict[str, List[str]]:
        """首页元素"""
        return {
            "create_btn": ["上传", "创作", "发布作品"],
            "message_btn": ["消息", "私信"],
            "profile_btn": ["我的", "个人主页", "我"],
        }

    @staticmethod
    def comment_page() -> Dict[str, List[str]]:
        """评论页面元素"""
        return {
            "comment_input": ["评论", "说点什么", "写评论"],
            "send_btn": ["发送", "发布", "评论"],
            "like_btn": ["点赞", "喜欢"],
        }


# 便捷函数
def find_element(keywords: List[str]) -> Optional[str]:
    """快速查找元素"""
    selector = Selector()
    nodes = selector.snap().get("nodes", [])
    return selector._find_element(nodes, keywords)


def click_element(ref: str) -> bool:
    """快速点击元素"""
    selector = Selector()
    return selector.click(ref)


def fill_input(ref: str, text: str) -> bool:
    """快速填写输入"""
    selector = Selector()
    return selector.fill(ref, text)