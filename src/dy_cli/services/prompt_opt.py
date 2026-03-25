"""
LLM 提示词优化服务
参考: https://github.com/cclank/lanshu-waytovideo
"""
from __future__ import annotations

import os
from typing import Optional, Protocol

from dy_cli.utils.config import get, load_config


# 优化系统提示词 - 基于 Seedance 提示词指南
OPTIMIZE_SYSTEM_PROMPT = """你是一个专业的视频生成提示词优化专家，精通 Seedance 2.0、即梦AI 等 AI 视频生成模型的提示词编写。

## 核心原则
**主体 + 动作 + 风格 + 镜头 + 环境**

## 提示词模板
```
[主体描述]，[动作/行为]，[画面风格]，[镜头语言]，[环境/光影]
```

## 优化要求
1. **主体明确**: 描述主体外观、特征、数量
2. **动作/行为**: 详细描述主体的动作、行为、表情
3. **画面风格**: 添加艺术风格如赛博朋克、水墨画、宫崎骏风格等
4. **镜头语言**:
   - 景别: 特写、近景、中景、远景、全景、鸟瞰
   - 运镜: 升降、推拉、环绕、穿越、慢动作
5. **环境/光影**:
   - 光线: 电影级光影、霓虹灯、月光、闪电
   - 氛围: 烟雾弥漫、雾气弥漫、背景虚化、水下摄影
6. **细节真实**: 补充真实的物理细节，如水滴、火焰、烟雾等

## 输出要求
- 仅返回优化后的提示词，不要输出解释
- 保持原意，增强表现力
- 如果原提示词已经很完善，可以微调后返回
- 长度控制在 100-300 字之间
- 使用中文描述"""


COMMENT_REPLY_SYSTEM_PROMPT = """你是短视频账号的评论助手。

要求：
1. 回复自然、简短、礼貌
2. 不承诺违规内容，不引导敏感行为
3. 面对负面评论保持克制
4. 最多 40 字

仅返回一条可直接发送的回复文本。"""


class LLMProvider(Protocol):
    """LLM Provider 协议"""

    def optimize_prompt(self, prompt: str) -> str:
        """优化视频生成提示词"""

    def generate_comment_reply(self, comment_text: str) -> str:
        """生成评论回复"""


class RuleBasedProvider:
    """基于规则的兜底 Provider - 参考 Seedance 提示词指南"""

    # 常用的镜头语言和氛围描述词
    SHOT_LANGUAGE = [
        "电影感构图", "主体清晰", "光影层次分明", "镜头平滑移动",
        "特写镜头", "中景镜头", "远景镜头", "全景镜头", "鸟瞰视角",
        "推镜", "拉镜", "升镜头", "降镜头", "环绕镜头",
    ]

    LIGHTING = [
        "自然光", "电影级光影", "霓虹灯光", "月光", "阳光",
        "暖色调", "冷色调", "逆光", "侧光", "轮廓光",
    ]

    ATMOSPHERE = [
        "烟雾弥漫", "雾气弥漫", "背景虚化", "景深",
        "水面波纹", "光影斑驳", "粒子效果",
    ]

    STYLE = [
        "写实风格", "电影感", "纪录片风格",
        "赛博朋克", "水墨画", "宫崎骏风格",
    ]

    def __init__(self, **kwargs):
        pass

    def optimize_prompt(self, prompt: str) -> str:
        prompt = prompt.strip()
        if not prompt:
            return prompt

        # 基于规则增强提示词
        enhanced = prompt

        # 添加镜头语言
        enhanced += f"，{self.SHOT_LANGUAGE[0]}，{self.SHOT_LANGUAGE[2]}"

        # 添加动作细节
        if "跑" in prompt or "走" in prompt:
            enhanced += "，步伐稳健"
        if "飞" in prompt or "漂浮" in prompt:
            enhanced += "，悬浮感"

        # 添加光影
        enhanced += f"，{self.LIGHTING[0]}，{self.ATMOSPHERE[1]}"

        return enhanced

    def generate_comment_reply(self, comment_text: str) -> str:
        text = comment_text or ""
        if any(k in text for k in ("怎么", "如何", "?", "？")):
            return "感谢关注，可以说下你更想看的方向，我后续安排。"
        if any(k in text for k in ("好", "赞", "棒", "喜欢")):
            return "谢谢支持，你的反馈是我持续更新的动力。"
        if any(k in text for k in ("差", "烂", "不行", "垃圾")):
            return "收到建议，我会继续优化内容质量，感谢直言。"
        return "感谢你的评论和关注。"


class OpenAIProvider:
    """OpenAI Provider"""

    def __init__(self, model: str = "gpt-4o", api_key: Optional[str] = None):
        try:
            from openai import OpenAI
        except ImportError:
            raise ImportError("openai package not installed. Run: pip install openai")

        self._client = OpenAI(api_key=api_key or os.getenv("OPENAI_API_KEY"))
        self._model = model

    def _chat(self, system: str, user: str, temperature: float = 0.7) -> str:
        response = self._client.chat.completions.create(
            model=self._model,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            temperature=temperature,
        )
        content = response.choices[0].message.content or ""
        return content.strip()

    def optimize_prompt(self, prompt: str) -> str:
        return self._chat(OPTIMIZE_SYSTEM_PROMPT, prompt, temperature=0.7)

    def generate_comment_reply(self, comment_text: str) -> str:
        return self._chat(COMMENT_REPLY_SYSTEM_PROMPT, comment_text, temperature=0.5)


class ClaudeProvider:
    """Anthropic Claude Provider"""

    def __init__(self, model: str = "claude-sonnet-4-20250514", api_key: Optional[str] = None):
        try:
            from anthropic import Anthropic
        except ImportError:
            raise ImportError("anthropic package not installed. Run: pip install anthropic")

        self._client = Anthropic(api_key=api_key or os.getenv("ANTHROPIC_API_KEY"))
        self._model = model

    def _chat(self, system: str, user: str, temperature: float = 0.7) -> str:
        response = self._client.messages.create(
            model=self._model,
            max_tokens=1024,
            system=system,
            messages=[{"role": "user", "content": user}],
            temperature=temperature,
        )
        content = response.content[0].text if response.content else ""
        return content.strip()

    def optimize_prompt(self, prompt: str) -> str:
        return self._chat(OPTIMIZE_SYSTEM_PROMPT, prompt, temperature=0.7)

    def generate_comment_reply(self, comment_text: str) -> str:
        return self._chat(COMMENT_REPLY_SYSTEM_PROMPT, comment_text, temperature=0.5)


class ProviderRegistry:
    """Provider 注册表"""

    def __init__(self):
        self._providers: dict[str, type] = {}
        self.register("rule", RuleBasedProvider)
        self.register("openai", OpenAIProvider)
        self.register("claude", ClaudeProvider)

    def register(self, name: str, provider_cls: type) -> None:
        self._providers[name.strip().lower()] = provider_cls

    def create(self, name: Optional[str] = None, **kwargs) -> LLMProvider:
        config = load_config()
        llm_cfg = config.get("llm", {})

        provider_name = (name or llm_cfg.get("provider", "openai")).strip().lower()
        provider_cls = self._providers.get(provider_name)

        if not provider_cls:
            raise ValueError(f"Unknown LLM provider: {provider_name}")

        try:
            model = kwargs.get("model") or llm_cfg.get("model", "gpt-4o")
            return provider_cls(model=model, **kwargs)
        except Exception:
            if provider_name == "rule":
                raise
            return RuleBasedProvider()

    def names(self) -> list[str]:
        return sorted(self._providers.keys())


_registry: Optional[ProviderRegistry] = None


def get_provider_registry() -> ProviderRegistry:
    global _registry
    if _registry is None:
        _registry = ProviderRegistry()
    return _registry


def get_provider(name: Optional[str] = None, **kwargs) -> LLMProvider:
    """获取 LLM Provider"""
    return get_provider_registry().create(name, **kwargs)


def optimize_prompt(prompt: str, provider: Optional[str] = None) -> str:
    """优化提示词"""
    p = get_provider(provider)
    return p.optimize_prompt(prompt)


def generate_comment_reply(comment_text: str, provider: Optional[str] = None) -> str:
    """生成评论回复"""
    p = get_provider(provider)
    return p.generate_comment_reply(comment_text)