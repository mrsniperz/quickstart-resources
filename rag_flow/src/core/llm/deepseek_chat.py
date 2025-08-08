import json
from typing import List, Dict, Union, Optional, Generator
from openai import OpenAI
import os
from src.utils.logger import SZ_LoggerManager

# 统一日志
logger = SZ_LoggerManager.get_logger(__name__)


class DeepSeekChat:
    def __init__(self, api_key: str, base_url: str = "https://api.deepseek.com"):
        self.client = OpenAI(api_key=api_key, base_url=base_url)
        self.reset_conversation()

    def reset_conversation(self):
        """开启全新对话"""
        self.messages = []
        self.tools = None
        self.tool_choice = None

    def chat(
        self,
        user_input: str,
        *,
        system_prompt: str = "",
        use_json: bool = False,
        max_history: Optional[int] = None,
        stream: bool = False,
        stream_callback: Optional[callable] = None,
        tools: Optional[List[Dict]] = None,
        tool_choice: Optional[Union[str, Dict]] = None,
        model: str = "deepseek-chat",
        **kwargs,
    ) -> Union[str, Dict, Generator]:
        """
        核心聊天方法

        参数:
            user_input: 用户输入内容
            system_prompt: 系统提示词 (default: "")
            use_json: 是否强制JSON输出 (default: False)
            max_history: 最大历史记录轮次，None表示不限制 (default: None)
            stream: 是否使用流式输出 (default: False)
            stream_callback: 流式输出的回调函数，接收单个token (default: None)
            tools: 工具调用定义列表 (default: None)
            tool_choice: 工具调用选择 (default: None)
            model: 模型名称 (default: "deepseek-chat")

        返回:
            非流式: 直接返回回复内容(JSON会被自动解析为dict)
            流式: 返回生成器或通过回调处理
        """
        # 1. 处理系统提示
        if system_prompt and (
            not self.messages or self.messages[0]["role"] != "system"
        ):
            if use_json and "json" not in system_prompt.lower():
                system_prompt += "\n(请用JSON格式输出)"
            self.messages.insert(0, {"role": "system", "content": system_prompt})

        # 2. 添加用户输入
        self.messages.append({"role": "user", "content": user_input})

        # 3. 处理历史记录限制
        if (
            max_history
            and len([m for m in self.messages if m["role"] in ("user", "assistant")])
            > max_history * 2
        ):
            self._summarize_history()

        # 4. 准备API参数
        api_params = {
            "model": model,
            "messages": self.messages,
            "stream": stream,
            **kwargs,
        }

        if use_json:
            api_params["response_format"] = {"type": "json_object"}
            api_params["stream"] = False
            if not any(
                "json" in m["content"].lower()
                for m in self.messages
                if isinstance(m.get("content"), str)
            ):
                self.messages[-1]["content"] += " (请用JSON格式回答)"

        if tools:
            api_params["tools"] = tools
            self.tools = tools
            if tool_choice:
                api_params["tool_choice"] = tool_choice
                self.tool_choice = tool_choice

        # 5. 调用API
        response = self.client.chat.completions.create(**api_params)

        # 如果使用json则只能普通输出
        if use_json:
            return self._handle_normal_response(response)

        # 6. 处理响应
        if stream:
            return self._handle_stream_response(response, stream_callback)
        else:
            return self._handle_normal_response(response)

    def _summarize_history(self):
        """总结历史对话以节省token"""
        summary_prompt = {
            "role": "user",
            "content": "请用中文简洁总结上述对话，保留所有关键事实和结论，不要遗漏重要数据。",
        }

        try:
            summary = (
                self.client.chat.completions.create(
                    model="deepseek-chat", messages=[*self.messages, summary_prompt]
                )
                .choices[0]
                .message.content
            )

            # 保留系统提示(如果有)和总结
            system_msg = [m for m in self.messages if m["role"] == "system"]
            self.messages = system_msg + [
                {"role": "assistant", "content": f"历史对话总结: {summary}"}
            ]
        except Exception as e:
            logger.warning(f"总结失败，继续完整历史记录: {e}")

    def _handle_normal_response(self, response):
        """处理普通响应"""
        message = response.choices[0].message

        # print(f'MESSAGE: {message.content}')

        # 处理工具调用
        if tool_calls := getattr(message, "tool_calls", None):
            self.messages.append(
                {"role": "assistant", "content": None, "tool_calls": tool_calls}
            )
            return {"tool_calls": tool_calls}

        # 处理普通回复
        self.messages.append({"role": "assistant", "content": message.content})

        try:
            return (
                json.loads(message.content)
                if message.content.startswith("{")
                else message.content
            )
        except json.JSONDecodeError:
            return message.content

    def _handle_stream_response(self, response, callback=None):
        """处理流式响应"""
        full_content = ""

        for chunk in response:
            if not chunk.choices:
                continue

            delta = chunk.choices[0].delta
            content = delta.content or ""

            full_content += content

            if callback:
                callback(content)
            else:
                yield content

        # 更新对话历史
        if full_content.strip():
            self.messages.append({"role": "assistant", "content": full_content})

    def add_tool_response(self, tool_name: str, tool_output: str):
        """添加工具调用结果到对话历史"""
        self.messages.append(
            {"role": "tool", "name": tool_name, "content": tool_output}
        )


# ============== 使用示例 ==============
if __name__ == "__main__":

    api_key = os.getenv("DEEPSEEK_API_KEY")

    # 1. 初始化
    chat = DeepSeekChat(api_key=api_key)

    # # 示例1: 普通多轮对话 (自动维护5轮历史)
    # print("=== 普通多轮对话 ===")
    # for i in range(6):
    #     response = chat.chat(
    #         f"这是第{i+1}个问题，请问答案是什么？",
    #         max_history=5  # 保持最多5轮对话历史
    #     )
    #     print(f"Round {i+1}:", response)

    # # 示例2: JSON格式输出
    # print("\n=== JSON格式输出 ===")
    # json_resp = chat.chat(
    #     "返回中国各省会城市的JSON字典，键为省名，值为省会",
    #     stream=True,
    # )
    # print(json_resp)  # 自动解析为字典

    # # 示例3: 流式输出 (两种方式)
    # print("\n=== 流式输出-直接处理 ===")
    # chat.reset_conversation()  # 新对话
    # for token in chat.chat("用100字介绍长城", stream=True):
    #     print(token, end="", flush=True)

    # print("\n\n=== 流式输出-回调处理 ===")
    # def callback(token):
    #     print(token, end="", flush=True)

    # chat.chat("再用100字介绍故宫", stream=True, stream_callback=callback)

    # # 测试纯流式（不涉及 JSON）
    # def callback(token):
    #     print("回调收到:", token, end="", flush=True)

    # chat.chat("你好，请说一句话", stream=True, stream_callback=callback)

    # # 示例4: 工具调用
    # print("\n\n=== 工具调用示例 ===")
    # weather_tool = {
    #     "type": "function",
    #     "function": {
    #         "name": "get_current_weather",
    #         "description": "获取当前天气",
    #         "parameters": {
    #             "type": "object",
    #             "properties": {
    #                 "location": {"type": "string", "description": "城市名称"}
    #             },
    #             "required": ["location"]
    #         }
    #     }
    # }

    # tool_response = chat.chat(
    #     "北京今天天气怎么样？",
    #     tools=[weather_tool]
    # )
    # print("工具调用请求:", tool_response)

    # # 模拟工具调用结果
    # chat.add_tool_response("get_current_weather", "北京: 晴, 25℃")
    # final_response = chat.chat("谢谢")
    # print("最终回复:", final_response)
