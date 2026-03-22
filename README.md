# 医保费用审判模拟器

Medical Trial Simulator for Medicare

## 项目简介

用 LLM 模拟医保审核官"审判"每笔费用，生成"起诉状"和"辩护词"，发现人工对账忽略的异常。

核心创新：将医保对账差异视为"案件"，用法律审判的视角解读每笔费用的"命运"。

## 功能特性

- 医保目录数据模型
- 费用明细与结算差异管理
- LLM 审判框架（起诉方、辩护方、法官）
- 完整的审判流程控制
- 多模型支持（Claude、GPT）
- CLI 命令行界面
- 批量审判功能
- 多格式报告输出（JSON、Markdown、HTML）

## 技术栈

- Python 3.9+
- LangChain（LLM 集成）
- Pydantic（数据模型）

## 安装

```bash
pip install -r requirements.txt
```

## 配置

### 环境变量

在项目根目录创建 `.env` 文件，配置 LLM API：

```bash
# Anthropic Claude（推荐）
ANTHROPIC_API_KEY=your_api_key_here

# OpenAI GPT（可选）
OPENAI_API_KEY=your_api_key_here

# 默认模型选择（claude 或 openai）
DEFAULT_MODEL=claude
```

### 配置文件示例

项目支持从环境变量或 `.env` 文件加载配置。配置优先级：
1. 环境变量
2. `.env` 文件
3. 代码默认值

### 批量配置

批量审判支持配置文件（JSON 格式）：

```json
{
  "model": "claude",
  "max_concurrent": 3,
  "retry_times": 2,
  "output_format": "markdown",
  "output_dir": "./results"
}
```

## 使用方法

```bash
# 单笔费用审判
python -m src.cli.main --expense data/sample_expenses.json

# 批量审判
python -m src.cli.main --batch data/sample_expenses.json

# 指定模型
python -m src.cli.main --model claude --expense data/sample_expenses.json

# 输出格式
python -m src.cli.main --expense data/sample_expenses.json --format markdown

# 使用示例数据进行审判
python -m src.cli.main --expense data/sample_expenses.json --format json

# 批量审判（审判多条费用差异）
python -m src.cli.main --batch data/sample_diffs.json

# 审判时指定输出文件
python -m src.cli.main --expense data/sample_expenses.json --output result.json

# 查看帮助
python -m src.cli.main --help
```

### 审判结果解读

审判结果包含三个角色：

1. **起诉方（Prosecutor）**：扮演医保审核规则，逐条指出费用不合规之处
   - 超标准收费
   - 超医保目录限制
   - 违反适应症
   - 重复收费等

2. **辩护方（Defense）**：扮演医院说明，解释费用合理性
   - 诊疗必要性和合理性说明
   - 医保目录适用解释
   - 特殊情况说明

3. **法官（Judge）**：综合双方意见，作出最终裁决
   - 采纳、部分采纳或驳回
   - 裁决理由
   - 扣款金额

### 示例数据说明

- `data/medicare_catalog.json`：医保目录数据，包含诊疗项目、药品、服务设施的医保报销标准
- `data/sample_expenses.json`：示例费用明细，模拟门诊/住院费用
- `data/sample_diffs.json`：示例结算差异，用于批量审判测试

## 项目结构

```
medical-trial-simulator/
├── src/
│   ├── models/          # 数据模型
│   ├── data/            # 数据处理
│   ├── prompts/         # LLM Prompt
│   ├── trial/           # 审判流程
│   ├── clients/         # LLM 客户端
│   └── cli/             # 命令行界面
├── data/                # 示例数据
├── requirements.txt
└── README.md
```

## 示例

### 审判流程示例

```
========== 医保费用审判 ==========
案件编号: CASE-2024-001

【起诉方】医保审核规则：
- 诊疗项目"核磁共振"超标准收费：标准300元，实际450元
- 药品"头孢类"超出医保目录限制适应症

【辩护方】医院说明：
- 核磁共振为增强检查，应执行增强检查收费标准
- 患者有感染指征，使用头孢类药物符合医保规定

【法官】裁决：
- 采纳辩护方意见，核磁共振增强检查符合规定
- 部分采纳辩护意见，扣除超出适应症部分费用50元
- 最终裁决：医院承担50元，其余合规

=================================
```

### 输出格式示例

#### JSON 输出

```json
{
  "case_id": "CASE-2024-001",
  "trial_date": "2024-01-15T10:30:00",
  "prosecutor": {
    "charges": [
      {
        "item": "核磁共振",
        "issue": "超标准收费",
        "standard_amount": 300,
        "actual_amount": 450
      }
    ]
  },
  "defense": {
    "arguments": [
      {
        "item": "核磁共振",
        "reason": "增强检查，应执行增强检查收费标准"
      }
    ]
  },
  "judge": {
    "verdict": "部分采纳",
    "reasoning": "核磁共振增强检查符合规定",
    "penalty": 50
  }
}
```

#### Markdown 输出

```markdown
# 医保费用审判报告

## 案件信息
- 案件编号：CASE-2024-001
- 审判时间：2024-01-15

## 起诉方（医保审核规则）
- 诊疗项目"核磁共振"超标准收费：标准300元，实际450元

## 辩护方（医院说明）
- 核磁共振为增强检查，应执行增强检查收费标准

## 法官裁决
- 采纳辩护方意见
- 裁决：医院承担50元，其余合规
```

## 许可证

MIT License

---

## 支持作者

如果您觉得这个项目对您有帮助，欢迎打赏支持！
Wechat:gdgdmp
![Buy Me a Coffee](buymeacoffee.png)

**Buy me a coffee (crypto)**

| 币种 | 地址 |
|------|------|
| BTC | `bc1qc0f5tv577z7yt59tw8sqaq3tey98xehy32frzd` |
| ETH / USDT | `0x3b7b6c47491e4778157f0756102f134d05070704` |
| SOL | `6Xuk373zc6x6XWcAAuqvbWW92zabJdCmN3CSwpsVM6sd` |
