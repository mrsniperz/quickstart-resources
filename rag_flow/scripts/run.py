#!/usr/bin/env python
"""
项目运行脚本

此脚本用于运行项目，支持不同的运行模式。
"""

import os
import sys
import argparse
import subprocess
from pathlib import Path

# 添加项目根目录到Python路径
ROOT_DIR = Path(__file__).parent.parent.absolute()
sys.path.insert(0, str(ROOT_DIR))


def parse_args():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description="项目运行脚本")
    parser.add_argument(
        "--mode", 
        choices=["dev", "prod", "test"], 
        default="dev",
        help="运行模式: dev(开发模式), prod(生产模式), test(测试模式)"
    )
    return parser.parse_args()


def run_dev():
    """开发模式运行"""
    print("以开发模式运行项目...")
    cmd = ["uv", "run", "python", "-m", "src.main"]
    subprocess.run(cmd)


def run_prod():
    """生产模式运行"""
    print("以生产模式运行项目...")
    # 设置生产环境变量
    os.environ["ENV"] = "production"
    cmd = ["uv", "run", "python", "-m", "src.main"]
    subprocess.run(cmd)


def run_test():
    """测试模式运行"""
    print("运行测试...")
    cmd = ["uv", "run", "pytest", "src/tests"]
    subprocess.run(cmd)


def main():
    """主函数"""
    args = parse_args()
    
    # 根据不同模式运行
    if args.mode == "dev":
        run_dev()
    elif args.mode == "prod":
        run_prod()
    elif args.mode == "test":
        run_test()
    else:
        print(f"不支持的运行模式: {args.mode}")
        sys.exit(1)


if __name__ == "__main__":
    main() 