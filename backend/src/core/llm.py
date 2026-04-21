"""
LLM 客户端抽象基类和实现
支持多种 LLM 后端：Ollama、Doubao API
"""

import json
from pathlib import Path
from typing import Dict, Optional
from abc import ABC, abstractmethod

import requests
from openai import OpenAI
from dotenv import load_dotenv

from ..config.settings import config

# 尝试导入 Ollama（可选）
try:
    import ollama
    OLLAMA_AVAILABLE = True
except ImportError:
    ollama = None
    OLLAMA_AVAILABLE = False

load_dotenv()


class BaseLLM(ABC):
    """LLM 客户端基类"""

    def __init__(self, model_name: str, system_prompt_path: str = None):
        self.model_name = model_name
        self.system_prompt = self._load_prompt(system_prompt_path)

    def _load_prompt(self, prompt_path: str = None) -> str:
        """加载系统提示词"""
        if prompt_path and Path(prompt_path).exists():
            with open(prompt_path, 'r', encoding='utf-8') as f:
                return f.read().strip()
        return ""

    @abstractmethod
    def chat(self, user_input: str, **kwargs) -> Dict:
        """发送聊天请求

        Args:
            user_input: 用户输入
            **kwargs: 其他参数

        Returns:
            响应字典
        """
        pass


class OllamaLLM(BaseLLM):
    """Ollama 本地模型"""

    def __init__(
        self,
        model_name: str = None,
        system_prompt_path: str = None,
        host: str = None,
        config = None
    ):
        model = model_name or config.OLLAMA_MODEL
        super().__init__(model, system_prompt_path)
        self.host = host or config.OLLAMA_HOST
        self._check_service()

    def _check_service(self):
        """检查 Ollama 服务"""
        try:
            ollama.list()
        except Exception as e:
            raise ConnectionError(
                f"无法连接到 Ollama 服务: {e}\n"
                "请确保：1. Ollama 已安装 2. 双击运行 Ollama 3. 执行 `ollama pull {self.model_name}`"
            )

    def chat(self, user_input: str, **kwargs) -> Dict:
        """发送聊天请求（支持多模态图片输入）"""
        temperature = kwargs.get('temperature', 0.8)
        num_predict = kwargs.get('num_predict', 800)
        image = kwargs.get('image')

        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": user_input}
        ]

        # 如果有图片，处理一下
        images = []
        if image:
            import base64
            from io import BytesIO
            
            buffered = BytesIO()
            image.save(buffered, format="JPEG")
            img_str = base64.b64encode(buffered.getvalue()).decode("utf-8")
            images = [img_str]

        response = ollama.chat(
            model=self.model_name,
            messages=messages,
            format="json",
            options={
                "temperature": temperature,
                "num_predict": num_predict
            },
            images=images
        )

        content = response['message']['content']

        # 优先检查是否是特定的无作物文本
        if self._check_exact_no_crop_message(content):
            raise Exception("该图片中不包含农作物")
        
        # 检查是否包含无作物提示
        if self._contains_no_crop_hint(content):
            raise Exception(f"该图片中不包含农作物: {content}")

        return json.loads(content)

    def _check_exact_no_crop_message(self, text: str) -> bool:
        """检查文本是否是精确的无作物消息（去空格后匹配）"""
        cleaned_text = text.strip()
        return cleaned_text == "该图片中不包含农作物"

    def _contains_no_crop_hint(self, text: str) -> bool:
        """检查文本是否包含无作物提示"""
        no_crop_keywords = [
            "未识别到需要诊断的农田作物",
            "没有作物",
            "无法诊断",
            "不包含作物",
            "没有农田作物",
            "不是作物图片"
        ]
        
        text_lower = text.lower()
        for keyword in no_crop_keywords:
            if keyword in text_lower:
                return True
        return False

    def chat_text(self, user_input: str, **kwargs) -> str:
        """普通文本聊天（不强制JSON格式）"""
        temperature = kwargs.get('temperature', 0.8)
        num_predict = kwargs.get('num_predict', 1000)
        history = kwargs.get('history', [])

        messages = [
            {"role": "system", "content": self.system_prompt}
        ]
        
        # 添加历史对话
        for msg in history:
            messages.append(msg)
        
        # 添加当前用户输入
        messages.append({"role": "user", "content": user_input})

        response = ollama.chat(
            model=self.model_name,
            messages=messages,
            options={
                "temperature": temperature,
                "num_predict": num_predict
            }
        )

        return response['message']['content']


class DoubaoLLM(BaseLLM):
    """字节跳动 Doubao API 大模型 (使用 OpenAI SDK)"""

    def __init__(
        self,
        model_name: str = None,
        system_prompt_path: str = None,
        api_key: str = None,
        base_url: str = None,
        debug: bool = True,
        config = None
    ):
        model = model_name or config.DOUBAO_MODEL
        super().__init__(model, system_prompt_path)
        self.api_key = api_key or config.DOUBAO_API_KEY
        self.base_url = base_url or config.DOUBAO_BASE_URL
        self.debug = debug
        self._check_config()
        self.client = OpenAI(
            base_url=self.base_url,
            api_key=self.api_key
        )

    def _check_config(self):
        """检查配置"""
        errors = []
        
        if not self.api_key:
            errors.append("- API Key 未设置 (DOUBAO_API_KEY)")
        
        if not self.model_name:
            errors.append("- 模型 ID 未设置 (DOUBAO_MODEL)")
        
        if errors:
            error_msg = "Doubao API 配置不完整:\n"
            error_msg += "\n".join(errors)
            error_msg += "\n\n配置步骤:\n"
            error_msg += "1. 访问 https://console.volcengine.com/ark\n"
            error_msg += "2. 创建推理接入点\n"
            error_msg += "3. 从接入点详情页获取模型 ID 和 API Key\n"
            error_msg += "4. 将配置填入 .env 文件"
            raise ValueError(error_msg)
        
        if self.debug:
            print(f"[Doubao] 配置检查完成")
            print(f"[Doubao] Base URL: {self.base_url}")
            print(f"[Doubao] 模型: {self.model_name}")

    def chat(self, user_input: str, **kwargs) -> Dict:
        """发送聊天请求到 Doubao API (支持多模态 Vision API)"""
        temperature = kwargs.get('temperature', 0.8)
        max_tokens = kwargs.get('max_tokens', 800)
        image = kwargs.get('image')

        if self.debug:
            print(f"[Doubao] 发送请求到: {self.base_url}")
            print(f"[Doubao] 模型: {self.model_name}")
            print(f"[Doubao] 是否包含图片: {'是' if image else '否'}")

        try:
            # 构建用户消息（支持图片+文字多模态）
            user_message_content = []
            
            # 添加文字内容
            user_message_content.append({
                "type": "text",
                "text": user_input
            })
            
            # 如果有图片，添加图片（base64编码）
            if image:
                import base64
                from io import BytesIO
                
                # 将 PIL 图片转为 base64
                buffered = BytesIO()
                image.save(buffered, format="JPEG")
                img_str = base64.b64encode(buffered.getvalue()).decode("utf-8")
                
                user_message_content.append({
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/jpeg;base64,{img_str}",
                        "detail": "high"
                    }
                })
                
                if self.debug:
                    print(f"[Doubao] 图片已编码: {len(img_str)} 字符")

            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": user_message_content}
                ],
                temperature=temperature,
                max_tokens=max_tokens
            )

            if self.debug:
                print(f"[Doubao] 请求成功")

            content = response.choices[0].message.content
            
            if self.debug:
                print(f"[Doubao] 完整返回内容:\n{content}\n")
                print(f"[Doubao] 开始检查内容...")

            # 优先检查是否是特定的无作物文本
            if self._check_exact_no_crop_message(content):
                raise Exception("该图片中不包含农作物")
            
            # 检查是否包含无作物提示
            if self._contains_no_crop_hint(content):
                raise Exception(f"该图片中不包含农作物: {content}")

            if self.debug:
                print(f"[Doubao] 开始提取 JSON...")
            return self._extract_json(content)

        except Exception as e:
            error_msg = f"Doubao API 请求失败: {e}"
            raise Exception(error_msg)

    def _check_exact_no_crop_message(self, text: str) -> bool:
        """检查文本是否是精确的无作物消息（去空格后匹配）"""
        cleaned_text = text.strip()
        return cleaned_text == "该图片中不包含农作物"

    def _contains_no_crop_hint(self, text: str) -> bool:
        """检查文本是否包含无作物提示"""
        no_crop_keywords = [
            "未识别到需要诊断的农田作物",
            "没有作物",
            "无法诊断",
            "不包含作物",
            "没有农田作物",
            "不是作物图片"
        ]
        
        text_lower = text.lower()
        for keyword in no_crop_keywords:
            if keyword in text_lower:
                return True
        return False

    def _extract_json(self, text: str) -> Dict:
        """从文本中提取 JSON 对象
        
        尝试多种方式提取 JSON，处理模型可能返回额外文本的情况
        """
        text = text.strip()
        
        try:
            if self.debug:
                print(f"[Doubao] 尝试方式1: 直接解析")
            return json.loads(text)
        except json.JSONDecodeError as e:
            if self.debug:
                print(f"[Doubao] 方式1失败: {e}")
        
        try:
            if self.debug:
                print(f"[Doubao] 尝试方式2: 查找 {{ 和 }}")
            start = text.find('{')
            end = text.rfind('}')
            if start != -1 and end != -1 and start < end:
                json_str = text[start:end+1]
                if self.debug:
                    print(f"[Doubao] 提取到的 JSON: {json_str}")
                return json.loads(json_str)
        except json.JSONDecodeError as e:
            if self.debug:
                print(f"[Doubao] 方式2失败: {e}")
        
        try:
            if self.debug:
                print(f"[Doubao] 尝试方式3: 查找 ```json 和 ```")
            start_marker = "```json"
            end_marker = "```"
            start = text.find(start_marker)
            if start != -1:
                start += len(start_marker)
                end = text.find(end_marker, start)
                if end != -1:
                    json_str = text[start:end].strip()
                    if self.debug:
                        print(f"[Doubao] 提取到的 JSON: {json_str}")
                    return json.loads(json_str)
        except json.JSONDecodeError as e:
            if self.debug:
                print(f"[Doubao] 方式3失败: {e}")
        
        # 如果所有方式都失败，抛出异常
        error_msg = f"无法从响应中提取有效的 JSON: {text}"
        raise json.JSONDecodeError(error_msg, text, 0)

    def chat_text(self, user_input: str, **kwargs) -> str:
        """普通文本聊天（不强制JSON格式）"""
        temperature = kwargs.get('temperature', 0.8)
        max_tokens = kwargs.get('max_tokens', 1000)
        history = kwargs.get('history', [])

        messages = [
            {"role": "system", "content": self.system_prompt}
        ]
        
        # 添加历史对话
        for msg in history:
            messages.append(msg)
        
        # 添加当前用户输入
        messages.append({"role": "user", "content": user_input})

        response = self.client.chat.completions.create(
            model=self.model_name,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens
        )

        return response.choices[0].message.content


def create_llm_client(provider: str = None, **kwargs) -> BaseLLM:
    """创建 LLM 客户端
    
    Args:
        provider: 提供商名称 (ollama, doubao)
        **kwargs: 传递给具体实现的参数
    
    Returns:
        LLM 客户端实例
    """
    provider = provider or config.ACTIVE_LLM
    
    if provider == "ollama":
        if not OLLAMA_AVAILABLE:
            raise ImportError("Ollama 不可用，请安装: pip install ollama")
        return OllamaLLM(config=config, **kwargs)
    
    elif provider == "doubao":
        return DoubaoLLM(config=config, **kwargs)
    
    else:
        raise ValueError(f"不支持的 LLM 提供商: {provider}")