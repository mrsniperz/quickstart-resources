import typer
from rich.console import Console
from rich.prompt import Prompt
import yaml
from typing import Optional, Dict, List
import json

app = typer.Typer()
console = Console()

class LangGPTPrompt:
    def __init__(self):
        self.sections = {
            "role": "",
            "profile": [],
            "rules": [],
            "workflow": [],
            "initialization": "",
            "constraints": [],
            "commands": [],
            "format": [],
            "examples": []
        }
    
    def to_yaml(self) -> str:
        return yaml.dump(self.sections, allow_unicode=True, sort_keys=False)

    def to_text(self) -> str:
        text = []
        
        # Role
        if self.sections["role"]:
            text.append(f"# Role: {self.sections['role']}\n")
        
        # Profile
        if self.sections["profile"]:
            text.append("## Profile\n")
            for item in self.sections["profile"]:
                text.append(f"- {item}")
            text.append("")
        
        # Rules
        if self.sections["rules"]:
            text.append("## Rules\n")
            for item in self.sections["rules"]:
                text.append(f"- {item}")
            text.append("")
        
        # Workflow
        if self.sections["workflow"]:
            text.append("## Workflow\n")
            for item in self.sections["workflow"]:
                text.append(f"- {item}")
            text.append("")
        
        # Initialization
        if self.sections["initialization"]:
            text.append(f"## Initialization\n{self.sections['initialization']}\n")
        
        # Constraints
        if self.sections["constraints"]:
            text.append("## Constraints\n")
            for item in self.sections["constraints"]:
                text.append(f"- {item}")
            text.append("")
        
        # Commands
        if self.sections["commands"]:
            text.append("## Commands\n")
            for item in self.sections["commands"]:
                text.append(f"- {item}")
            text.append("")
        
        # Format
        if self.sections["format"]:
            text.append("## Format\n")
            for item in self.sections["format"]:
                text.append(f"- {item}")
            text.append("")
        
        # Examples
        if self.sections["examples"]:
            text.append("## Examples\n")
            for item in self.sections["examples"]:
                text.append(f"- {item}")
            text.append("")
        
        return "\n".join(text)

def get_multiline_input(prompt: str) -> str:
    console.print(f"\n{prompt} (输入空行结束):", style="bold green")
    lines = []
    while True:
        line = input()
        if line.strip() == "":
            break
        lines.append(line)
    return "\n".join(lines)

def get_list_input(prompt: str) -> List[str]:
    console.print(f"\n{prompt} (每行一项，输入空行结束):", style="bold green")
    items = []
    while True:
        line = input()
        if line.strip() == "":
            break
        items.append(line)
    return items

@app.command()
def create_prompt():
    """创建新的 LangGPT 格式的 prompt"""
    prompt = LangGPTPrompt()
    
    console.print("欢迎使用 LangGPT Prompt 助手！", style="bold blue")
    console.print("请按照提示填写各个部分的内容。\n", style="blue")
    
    # 获取各个部分的输入
    prompt.sections["role"] = Prompt.ask("请输入角色描述")
    prompt.sections["profile"] = get_list_input("请输入角色属性列表")
    prompt.sections["rules"] = get_list_input("请输入规则列表")
    prompt.sections["workflow"] = get_list_input("请输入工作流程列表")
    prompt.sections["initialization"] = get_multiline_input("请输入初始化信息")
    prompt.sections["constraints"] = get_list_input("请输入约束条件列表")
    prompt.sections["commands"] = get_list_input("请输入命令列表")
    prompt.sections["format"] = get_list_input("请输入格式要求列表")
    prompt.sections["examples"] = get_list_input("请输入示例列表")
    
    # 输出结果
    console.print("\n生成的 Prompt:", style="bold green")
    console.print(prompt.to_text())
    
    # 保存结果
    output_format = Prompt.ask("请选择输出格式", choices=["text", "yaml"], default="text")
    filename = Prompt.ask("请输入保存的文件名", default="prompt")
    
    if output_format == "text":
        filename = f"{filename}.txt"
        with open(filename, "w", encoding="utf-8") as f:
            f.write(prompt.to_text())
    else:
        filename = f"{filename}.yaml"
        with open(filename, "w", encoding="utf-8") as f:
            f.write(prompt.to_yaml())
    
    console.print(f"\nPrompt 已保存到 {filename}", style="bold green")

if __name__ == "__main__":
    app() 