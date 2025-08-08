"""LLM模型选择与调用模块

功能描述: 
- 提供统一的接口调用DeepSeek和GLM系列模型
- 支持常用参数控制和流式输出
- 处理不同API的差异

创建日期: 2025-05-24
作者: Sniperz
版本: 1.1.1
"""
import os
from typing import Optional, Dict, Any, Iterator, Union
import logging
import json
import re
from openai import OpenAI
from zhipuai import ZhipuAI
from src.utils.logger import SZ_LoggerManager
from json_repair import repair_json

# 配置日志
logger = SZ_LoggerManager.get_logger(__name__)

# 环境变量名称
ENV_DS_API_KEY = "DS_API_KEY"
ENV_ZHIPU_API_KEY = "ZHIPU_API_KEY"
ENV_KIMI_API_KEY = "KIMI_API_KEY"  # 新增Kimi API密钥环境变量
ENV_OPENAI_API_KEY = "OPENAI_API_KEY"  # OpenAI SDK默认环境变量名

def try_parse_json_object(input_str: str) -> tuple[str, dict]:
    """JSON字符串解析和修复工具
    
    Args:
        input_str: 可能包含JSON的字符串
        
    Returns:
        (处理后的字符串, 解析后的字典)
    """
    # 直接尝试解析
    try:
        result = json.loads(input_str)
        if isinstance(result, dict):
            return input_str, result
    except json.JSONDecodeError:
        logger.info("检测到JSON解析错误，尝试修复")

    # 清理Markdown代码块标记
    processed_input = input_str
    if processed_input.startswith("```json"):
        processed_input = processed_input[len("```json"):]
    elif processed_input.startswith("```"):
        processed_input = processed_input[len("```"):]
    
    if processed_input.endswith("```"):
        processed_input = processed_input[:-len("```")]
    
    processed_input = processed_input.strip()

    # 再次尝试解析清理后的字符串
    try:
        result = json.loads(processed_input)
        if isinstance(result, dict):
            return processed_input, result
    except json.JSONDecodeError:
        # 使用json_repair进行修复
        try:
            repaired_str = repair_json(json_str=processed_input, return_objects=False)
            result = json.loads(repaired_str)
            
            if not isinstance(result, dict):
                logger.warning(f"JSON修复成功但结果不是字典类型: {type(result)}")
                return repaired_str, {}
            return repaired_str, result
        except Exception as e:
            logger.exception(f"JSON修复失败: {e}, 原始输入: '{processed_input}'")
            return processed_input, {}

    return processed_input, {}  # 理论上不会执行到这里

class LLMClient:
    """LLM模型客户端封装类"""
    
    # 支持的模型映射
    MODEL_MAPPING = {
        "deepseek-chat": "deepseek-chat",
        # —— GLM4 文本模型 ——
        "glm-4-plus": "glm-4-plus",
        "glm-4-air": "glm-4-air-250414",
        "glm-4-airx": "glm-4-airx",
        "glm-4-flash": "glm-4-flash-250414",
        "glm-4-flashx": "glm-4-flashx-250414",
        # （可选）新版本占位："glm-4.5": "glm-4.5",
        # —— GLM 视觉模型 ——
        "glm-4.1v-thinking-flash": "glm-4.1v-thinking-flash",
        "glm-4.1v-thinking-flashx": "glm-4.1v-thinking-flashx",
        # 历史视觉型号（如仍开放可直接调用）
        "glm-4v-plus-0111": "glm-4v-plus-0111",
        # 新增Kimi模型映射
        "kimi-k2-0711-preview": "kimi-k2-0711-preview",
        "kimi-k2-turbo-preview": "kimi-k2-turbo-preview",
        "kimi-thinking-preview": "kimi-thinking-preview",
        # 新增Kimi视觉模型
        "kimi-vision": "moonshot-v1-8k-vision-preview"
    }
    
    def __init__(self):
        """初始化客户端配置"""
        # 获取API密钥
        self.ds_api_key = os.environ.get(ENV_DS_API_KEY)
        self.zhipu_api_key = os.environ.get(ENV_ZHIPU_API_KEY)
        self.kimi_api_key = os.environ.get(ENV_KIMI_API_KEY)  # 新增Kimi API密钥
        
        # API基础URL
        self.ds_base_url = "https://api.deepseek.com"
        self.zhipu_base_url = "https://open.bigmodel.cn/api/paas/v4/"
        self.kimi_base_url = "https://api.moonshot.cn/v1"  # 新增Kimi API基础URL
        
        # 验证API密钥是否存在
        if not self.ds_api_key:
            logger.warning(f"未找到DeepSeek API密钥({ENV_DS_API_KEY}环境变量)，DeepSeek模型将无法使用")
        
        if not self.zhipu_api_key:
            logger.warning(f"未找到智谱API密钥({ENV_ZHIPU_API_KEY}环境变量)，GLM模型将无法使用")
        
        if not self.kimi_api_key:
            logger.warning(f"未找到Kimi API密钥({ENV_KIMI_API_KEY}环境变量)，Kimi模型将无法使用")
        
        # 为了兼容OpenAI SDK，将DeepSeek密钥设置为OPENAI_API_KEY环境变量
        # 注意：这只会在当前进程中设置，不会影响系统环境变量
        self._original_openai_key = os.environ.get(ENV_OPENAI_API_KEY)

    def _get_client(self, model_name: str) -> Union[OpenAI, ZhipuAI]:
        """根据模型名称获取对应的客户端"""
        if model_name == "deepseek-chat":
            if not self.ds_api_key:
                raise ValueError(f"DeepSeek API密钥未设置，请设置{ENV_DS_API_KEY}环境变量")
            
            # 使用api_key参数直接传递，而不依赖环境变量
            return OpenAI(api_key=self.ds_api_key, base_url=self.ds_base_url)
        
        elif self._is_glm_model(model_name):
            if not self.zhipu_api_key:
                raise ValueError(f"智谱API密钥未设置，请设置{ENV_ZHIPU_API_KEY}环境变量")
            
            return ZhipuAI(api_key=self.zhipu_api_key)
        
        elif model_name in ("kimi-k2-0711-preview", "kimi-k2-turbo-preview", "kimi-thinking-preview", "kimi-vision"):
            if not self.kimi_api_key:
                raise ValueError(f"Kimi API密钥未设置，请设置{ENV_KIMI_API_KEY}环境变量")
            
            # Kimi使用OpenAI SDK，配置专用的base_url
            return OpenAI(api_key=self.kimi_api_key, base_url=self.kimi_base_url)
        else:
            raise ValueError(f"不支持的模型: {model_name}")

    def _get_model_id(self, model_name: str) -> str:
        """获取模型对应的实际ID"""
        return self.MODEL_MAPPING.get(model_name, "deepseek-chat")
    
    def _add_json_hint(self, messages: list, model_name: str) -> list:
        """为消息添加JSON格式提示
        
        Args:
            messages: 原始消息列表
            model_name: 模型名称
            
        Returns:
            添加了JSON提示的消息列表
        """
        processed_messages = [msg.copy() for msg in messages]
        
        # 根据不同模型选择适当的JSON提示
        json_hint = "请用JSON格式输出。"
        if self._is_glm_model(model_name):
            json_hint = "\n请务必以JSON格式返回响应，不要包含任何Markdown标记或额外文本。"

        # 尝试添加到system消息
        if processed_messages and processed_messages[0]["role"] == "system":
            if 'JSON' not in processed_messages[0]["content"]:
                processed_messages[0]["content"] += f"\n{json_hint}"
            return processed_messages
        
        # 尝试添加到最后一条用户消息
        for i in range(len(processed_messages) - 1, -1, -1):
            if processed_messages[i]["role"] == "user":
                if 'JSON' not in processed_messages[i]["content"]:
                    processed_messages[i]["content"] += f"\n{json_hint}"
                return processed_messages
        
        # 如果没有用户消息，添加新的用户消息
        processed_messages.append({"role": "user", "content": json_hint})
        return processed_messages

    def _is_vision_model(self, model_name: str) -> bool:
        """判断是否为视觉模型（Kimi 与 GLM 视觉型号）"""
        glm_vision = {
            "glm-4.1v-thinking-flash",
            "glm-4.1v-thinking-flashx",
            "glm-4v-plus-0111",
        }
        return model_name == "kimi-vision" or model_name in glm_vision
    
    def _is_kimi_model(self, model_name: str) -> bool:
        """判断是否为Kimi模型"""
        return model_name in ("kimi-k2-0711-preview", "kimi-k2-turbo-preview", "kimi-thinking-preview", "kimi-vision")
    
    def _is_glm_model(self, model_name: str) -> bool:
        """判断是否为GLM（智谱）模型（文本或多模态）"""
        return model_name.startswith("glm-")

    def build_vision_messages(self, text: str, image_urls: list[str]) -> list:
        """构造多模态（文本+图片）消息，兼容GLM与Kimi视觉接口
        
        Args:
            text: 文本提示
            image_urls: 图片URL列表
        Returns:
            messages: 可直接传入chat_completion的messages
        """
        contents = []
        if text:
            contents.append({"type": "text", "text": text})
        for u in image_urls or []:
            contents.append({"type": "image_url", "image_url": {"url": u}})
        return [{"role": "user", "content": contents}]
    
    def _adapt_kimi_tool_choice(self, tool_choice: Optional[str], **kwargs) -> Dict[str, Any]:
        """适配Kimi模型的tool_choice参数
        
        Kimi API不支持tool_choice="required"，需要特殊处理
        """
        adapted_kwargs = kwargs.copy()
        
        if tool_choice == "required":
            # Kimi不支持required，改为auto，并在后续处理中添加引导
            adapted_kwargs["tool_choice"] = "auto"
            adapted_kwargs["_kimi_force_tool_call"] = True
        elif tool_choice in ("none", "auto", None):
            adapted_kwargs["tool_choice"] = tool_choice
        else:
            # 其他值保持不变
            adapted_kwargs["tool_choice"] = tool_choice
            
        return adapted_kwargs

    def generate_translation_template(self, system_var: str, reference: str, query: str) -> list:
        """生成翻译任务的消息模板"""
        return [
            {"role": "system", "content": f"{system_var}"},
            {
                "role": "user",
                "content": f'''
                <REFERENCE>
                {reference}
                </REFERENCE>

                <USER'S QUERY>
                {query}
                </USER'S QUERY>
                '''
            }
        ]

    def chat_completion(
        self,
        messages: list,
        model_name: str = "deepseek-chat",
        temperature: float = 1.0,
        max_tokens: Optional[int] = None,
        top_p: float = 1.0,
        frequency_penalty: float = 0.0,
        presence_penalty: float = 0.0,
        stop: Optional[Union[str, list]] = None,
        stream: bool = True,
        use_json: bool = False,
        enable_vision: bool = False,
        tools: Optional[list] = None,
        tool_choice: Optional[str] = None,
        **kwargs
    ) -> Union[str, Iterator[str], Dict[str, Any]]:
        """统一的聊天补全接口
        
        Args:
            messages: 消息列表
            model_name: 模型名称
            temperature: 温度参数
            max_tokens: 最大token数
            top_p: top_p参数
            frequency_penalty: 频率惩罚
            presence_penalty: 存在惩罚
            stop: 停止词
            stream: 是否流式输出
            use_json: 是否使用JSON格式
            enable_vision: 是否启用视觉识别（仅对支持的模型有效）
            tools: 工具列表（用于tool calls）
            tool_choice: 工具选择策略
            **kwargs: 其他参数
        """
        # 视觉模型检查
        if enable_vision and not self._is_vision_model(model_name):
            if self._is_kimi_model(model_name):
                # 如果是Kimi模型但不是视觉模型，自动切换到视觉模型
                logger.info(f"启用视觉识别，自动切换到Kimi视觉模型")
                model_name = "kimi-vision"
            elif self._is_glm_model(model_name):
                # GLM 文本模型不直接切换，提示使用视觉型号
                logger.warning(
                    f"模型 {model_name} 非视觉型号。请使用 'glm-4.1v-thinking-flashx' 或 'glm-4.1v-thinking-flash' 等视觉模型。"
                )
            else:
                logger.warning(f"模型 {model_name} 不支持视觉识别，忽略 enable_vision 参数")
        # JSON模式下强制非流式
        if use_json and stream:
            logger.warning("use_json=True 时，强制 stream=False")
            stream = False

        try:
            client = self._get_client(model_name)
            model_id = self._get_model_id(model_name)
            
            # 处理消息
            processed_messages = [msg.copy() for msg in messages]
            if use_json:
                processed_messages = self._add_json_hint(processed_messages, model_name)

            # 多模态辅助：当 enable_vision 且传入 image_urls/vision_text 时，自动构造视觉消息
            if enable_vision and self._is_vision_model(model_name):
                image_urls = kwargs.pop("image_urls", None)
                vision_text = kwargs.pop("vision_text", None)
                if image_urls:
                    # 若用户已有user消息，将其文本并入
                    last_user_idx = next((i for i in range(len(processed_messages)-1, -1, -1)
                                          if processed_messages[i].get("role") == "user"), None)
                    base_text = vision_text
                    if base_text is None and last_user_idx is not None:
                        base_text = processed_messages[last_user_idx].get("content", "")
                        if isinstance(base_text, list):
                            # 已是多模态，直接附加图片
                            contents = base_text + [
                                {"type": "image_url", "image_url": {"url": u}} for u in image_urls
                            ]
                            processed_messages[last_user_idx]["content"] = contents
                            base_text = None
                        elif not isinstance(base_text, str):
                            base_text = ""
                    if base_text is not None:
                        processed_messages = self.build_vision_messages(base_text, image_urls)

            # 构造基本请求参数
            params = {
                "model": model_id,
                "messages": processed_messages,
                "temperature": temperature,
                "top_p": top_p,
                "stream": stream 
            }
            
            # 添加可选参数
            if max_tokens is not None:
                params["max_tokens"] = max_tokens
            if stop is not None:
                params["stop"] = stop
            
            # 添加模型特定参数
            if model_name == "deepseek-chat":
                params["frequency_penalty"] = frequency_penalty
                params["presence_penalty"] = presence_penalty
            
            # 设置JSON输出格式
            if use_json:
                params["response_format"] = {"type": "json_object"}
            
            # 处理工具调用参数
            if tools is not None:
                params["tools"] = tools
                
                # 适配Kimi模型的tool_choice
                if self._is_kimi_model(model_name):
                    adapted_kwargs = self._adapt_kimi_tool_choice(tool_choice, **kwargs)
                    if "tool_choice" in adapted_kwargs:
                        params["tool_choice"] = adapted_kwargs["tool_choice"]
                    # 保存是否需要强制工具调用的标记
                    force_tool_call = adapted_kwargs.get("_kimi_force_tool_call", False)
                else:
                    if tool_choice is not None:
                        params["tool_choice"] = tool_choice
                    force_tool_call = False
            else:
                force_tool_call = False
            
            # 添加其他自定义参数（排除内部标记）
            # 过滤内部或辅助参数，避免传入API产生错误
            drop_keys = {"image_urls", "vision_text"}
            filtered_kwargs = {k: v for k, v in kwargs.items() if (not k.startswith("_")) and (k not in drop_keys)}
            params.update(filtered_kwargs)
            
            # 调用API
            response = client.chat.completions.create(**params)
            
            # 处理Kimi模型的强制工具调用
            if (force_tool_call and not stream and 
                hasattr(response, 'choices') and response.choices and 
                response.choices[0].finish_reason != "tool_calls"):
                
                logger.info("Kimi模型未自动调用工具，添加引导消息")
                # 添加引导消息
                processed_messages.append(response.choices[0].message.dict())
                processed_messages.append({
                    "role": "user",
                    "content": "请选择一个工具（tool）来处理当前的问题。"
                })
                
                # 重新调用，不再强制工具调用
                params["messages"] = processed_messages
                if "tool_choice" in params:
                    params["tool_choice"] = "auto"
                
                response = client.chat.completions.create(**params)
            
            # 处理响应
            if stream:
                # 流式输出
                def generate():
                    for chunk in response:
                        if chunk.choices and chunk.choices[0].delta.content:
                            yield chunk.choices[0].delta.content
                return generate()
            else:
                # 非流式输出
                if use_json:
                    content = response.choices[0].message.content
                    if content:
                        # 尝试解析和修复JSON
                        _, parsed_json = try_parse_json_object(content)
                        return parsed_json
                    return {}
                else:
                    return response.choices[0].message.content or ""
                
        except Exception as e:
            logger.error(f"调用{model_name}模型时出错: {str(e)}")
            raise

# 全局客户端实例
llm_client = LLMClient()

def chat_completion(
    messages: list,
    model_name: str = "deepseek-chat",
    temperature: float = 0.3,
    max_tokens: Optional[int] = None,
    top_p: float = 1.0,
    frequency_penalty: float = 0.0,
    presence_penalty: float = 0.0,
    stop: Optional[Union[str, list]] = None,
    stream: bool = False,
    use_json: bool = False,
    enable_vision: bool = False,
    tools: Optional[list] = None,
    tool_choice: Optional[str] = None,
    **kwargs
) -> Union[str, Iterator[str], Dict[str, Any]]:
    """简化版的聊天补全接口"""
    return llm_client.chat_completion(
        messages=messages,
        model_name=model_name,
        temperature=temperature,
        max_tokens=max_tokens,
        top_p=top_p,
        frequency_penalty=frequency_penalty,
        presence_penalty=presence_penalty,
        stop=stop,
        stream=stream,
        use_json=use_json,
        enable_vision=enable_vision,
        tools=tools,
        tool_choice=tool_choice,
        **kwargs
    )

# 提供一个辅助设置API密钥的函数
def set_api_keys(deepseek_api_key: Optional[str] = None, zhipu_api_key: Optional[str] = None, kimi_api_key: Optional[str] = None) -> None:
    """手动设置API密钥
    
    当无法通过环境变量设置API密钥时，可以使用此函数手动设置
    
    Args:
        deepseek_api_key: DeepSeek API密钥
        zhipu_api_key: 智谱API密钥
        kimi_api_key: Kimi API密钥
    """
    global llm_client
    
    if deepseek_api_key:
        llm_client.ds_api_key = deepseek_api_key
        logger.info("已手动设置DeepSeek API密钥")
        
    if zhipu_api_key:
        llm_client.zhipu_api_key = zhipu_api_key
        logger.info("已手动设置智谱API密钥")
    
    if kimi_api_key:
        llm_client.kimi_api_key = kimi_api_key
        logger.info("已手动设置Kimi API密钥")
