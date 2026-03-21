# 医疗法庭审判模拟器 (Medical Trial Simulator)

用 LLM 模拟医疗事故法庭审判流程。输入病历后，AI 分别扮演原告（指控病历缺陷）、被告（病历辩护）、法官（裁决）、陪审团（综合意见），生成审判记录和多维度质量评估报告。

## 功能特性

- **AI 角色扮演**：原告律师、被告（病历）、法官、陪审团四方对抗
- **多维度评估**：完整性、逻辑一致性、规范符合度、证据支持度、时间线准确性
- **双模式**：Web 界面 (Streamlit) 和命令行接口
- **灵活配置**：支持 OpenAI 和 Anthropic API

## 快速开始

### 安装

```bash
pip install -r requirements.txt
```

### 配置 API Key

创建 `.env` 文件：

```bash
# 选择其中一个
OPENAI_API_KEY=your_openai_key
ANTHROPIC_API_KEY=your_anthropic_key
```

或者使用 `.env.example` 作为参考。

### 运行

**Web 界面：**
```bash
streamlit run app.py
```

**命令行：**
```bash
python main.py --input "病历内容..." --output report.json
```

## 项目结构

```
medical-trial-simulator/
├── app.py              # Streamlit Web 应用
├── main.py             # CLI 入口
├── requirements.txt    # 依赖
├── .gitignore          # Git 忽略配置
├── README.md           # 本文件
├── buymeacoffee.png    # 打赏图片
├── src/
│   ├── llm_client.py   # LLM 客户端封装
│   ├── prompts.py      # 角色 Prompt 模板
│   ├── trial.py        # 审判流程逻辑
│   ├── evaluator.py    # 病历评估器
│   └── report.py       # 报告生成器
├── data/
│   └── sample_cases/   # 示例病历
└── tests/              # 单元测试
```

## 使用示例

### Web 界面

1. 运行 `streamlit run app.py`
2. 在左侧配置 API Key
3. 输入或选择示例病历
4. 点击"开始审判"按钮
5. 查看审判流程和评估报告

### 命令行

```bash
# 从文件输入病历
python main.py --input data/sample_cases/case1.txt --output report.json

# 直接输入病历
python main.py --input "患者主诉：..." --model gpt-4o
```

## 评估维度

| 维度 | 说明 |
|------|------|
| 完整性 | 病历是否包含必要的信息项 |
| 逻辑一致性 | 诊断、治疗、用药等是否存在逻辑矛盾 |
| 规范符合度 | 是否符合医疗文书规范 |
| 证据支持度 | 诊疗措施是否有对应记录支持 |
| 时间线准确性 | 时间记录是否准确、连续 |

## 技术栈

- **Python 3.10+**
- **Streamlit** - Web 界面
- **OpenAI / Anthropic** - LLM 能力

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
