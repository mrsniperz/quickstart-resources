# Python项目模板

## 项目简介
这是一个基于规范创建的Python项目模板，使用uv作为包管理工具。

## 目录结构
```
./
├── src/               # 源代码
│   ├── core/          # 核心功能
│   ├── utils/         # 工具函数
│   └── tests/         # 测试文件
├── docs/              # 项目文档
│   ├── 研发工作量评估/
│   ├── 需求规格说明书/
│   ├── 概要设计说明书/
│   └── 详细设计说明书/
├── scripts/           # 脚本文件
├── config/            # 配置文件
├── .github/           # CI/CD 配置
├── pyproject.toml     # 项目配置
└── README.md          # 项目说明
```

## 环境配置
本项目使用uv进行包管理和环境管理。

### 安装uv
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### 创建虚拟环境
```bash
uv venv
```

### 安装依赖
```bash
uv pip install -e .
```

### 运行项目
```bash
uv run python -m src.main
```

## 开发规范
请参考项目中的代码规范文档进行开发。

## 文档
- [研发工作量评估](docs/研发工作量评估/README.md)
- [需求规格说明书](docs/需求规格说明书/README.md)
- [概要设计说明书](docs/概要设计说明书/README.md)
- [详细设计说明书](docs/详细设计说明书/README.md)
