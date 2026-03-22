# Medical Trial Simulator for Medicare

Medical Trial Simulator for Medicare

## Project Overview

Use LLM to simulate Medicare auditors "trialing" each expense, generating "indictments" and "defense arguments" to discover anomalies that manual reconciliation misses.

Core Innovation: Treat Medicare reconciliation differences as "cases" and interpret each expense's "fate" from the perspective of legal trial.

## Features

- Medicare catalog data model
- Expense details and settlement difference management
- LLM trial framework (Prosecutor, Defense, Judge)
- Complete trial process control
- Multi-model support (Claude, GPT)
- CLI command-line interface
- Batch trial functionality
- Multi-format report output (JSON, Markdown, HTML)

## Tech Stack

- Python 3.9+
- LangChain (LLM integration)
- Pydantic (data models)

## Installation

```bash
pip install -r requirements.txt
```

## Configuration

### Environment Variables

Create a `.env` file in the project root to configure LLM API:

```bash
# Anthropic Claude (recommended)
ANTHROPIC_API_KEY=your_api_key_here

# OpenAI GPT (optional)
OPENAI_API_KEY=your_api_key_here

# Default model selection (claude or openai)
DEFAULT_MODEL=claude
```

### Configuration File Example

The project supports loading configuration from environment variables or `.env` file. Configuration priority:
1. Environment variables
2. `.env` file
3. Code default values

### Batch Configuration

Batch trial supports configuration files (JSON format):

```json
{
  "model": "claude",
  "max_concurrent": 3,
  "retry_times": 2,
  "output_format": "markdown",
  "output_dir": "./results"
}
```

## Usage

```bash
# Single expense trial
python -m src.cli.main --expense data/sample_expenses.json

# Batch trial
python -m src.cli.main --batch data/sample_expenses.json

# Specify model
python -m src.cli.main --model claude --expense data/sample_expenses.json

# Output format
python -m src.cli.main --expense data/sample_expenses.json --format markdown

# Trial with sample data
python -m src.cli.main --expense data/sample_expenses.json --format json

# Batch trial (trial multiple expense differences)
python -m src.cli.main --batch data/sample_diffs.json

# Specify output file during trial
python -m src.cli.main --expense data/sample_expenses.json --output result.json

# View help
python -m src.cli.main --help
```

### Trial Result Interpretation

Trial results contain three roles:

1. **Prosecutor**: Plays the role of Medicare audit rules, pointing out each non-compliance issue
   - Over-standard charges
   - Exceeding Medicare catalog limits
   - Off-label usage
   - Duplicate charges, etc.

2. **Defense**: Plays the role of hospital explanations, justifying the expense rationality
   - Explanation of diagnosis/treatment necessity and reasonableness
   - Medicare catalog applicability explanation
   - Special circumstances explanation

3. **Judge**: Synthesizes both parties' opinions, makes final ruling
   - Accept, partially accept, or reject
   - Reasoning for ruling
   - Deduction amount

### Sample Data Description

- `data/medicare_catalog.json`: Medicare catalog data, including medical items, drugs, and service facility Medicare reimbursement standards
- `data/sample_expenses.json`: Sample expense details, simulating outpatient/inpatient expenses
- `data/sample_diffs.json`: Sample settlement differences, used for batch trial testing

## Project Structure

```
medical-trial-simulator/
├── src/
│   ├── models/          # Data models
│   ├── data/            # Data processing
│   ├── prompts/         # LLM prompts
│   ├── trial/           # Trial process
│   ├── clients/         # LLM clients
│   └── cli/             # Command-line interface
├── data/                # Sample data
├── requirements.txt
└── README.md
```

## Examples

### Trial Process Example

```
========== Medicare Expense Trial ==========
Case ID: CASE-2024-001

【Prosecutor】Medicare Audit Rules:
- Medical item "MRI" over-standard charge: standard 300 yuan, actual 450 yuan
- Drug "Cephalosporin" exceeds Medicare catalog limit indications

【Defense】Hospital Explanation:
- MRI is an enhanced examination, should follow enhanced examination收费标准
- Patient has infection indication, use of cephalosporin complies with Medicare regulations

【Judge】Ruling:
- Accept defense argument, MRI enhanced examination complies with regulations
- Partially accept defense argument, deduct 50 yuan for exceeding indication portion
- Final ruling: Hospital bears 50 yuan, rest is compliant

=================================
```

### Output Format Example

#### JSON Output

```json
{
  "case_id": "CASE-2024-001",
  "trial_date": "2024-01-15T10:30:00",
  "prosecutor": {
    "charges": [
      {
        "item": "MRI",
        "issue": "Over-standard charge",
        "standard_amount": 300,
        "actual_amount": 450
      }
    ]
  },
  "defense": {
    "arguments": [
      {
        "item": "MRI",
        "reason": "Enhanced examination, should follow enhanced examination charging standard"
      }
    ]
  },
  "judge": {
    "verdict": "Partially Accept",
    "reasoning": "MRI enhanced examination complies with regulations",
    "penalty": 50
  }
}
```

#### Markdown Output

```markdown
# Medicare Expense Trial Report

## Case Information
- Case ID: CASE-2024-001
- Trial Date: 2024-01-15

## Prosecutor (Medicare Audit Rules)
- Medical item "MRI" over-standard charge: standard 300 yuan, actual 450 yuan

## Defense (Hospital Explanation)
- MRI is an enhanced examination, should follow enhanced examination charging standard

## Judge Ruling
- Accept defense argument
- Ruling: Hospital bears 50 yuan, rest is compliant
```

## License

MIT License

---

## Support the Author

If you find this project helpful, feel free to buy me a coffee! ☕

![Buy Me a Coffee](buymeacoffee.png)

**Buy me a coffee (crypto)**

| Chain | Address |
|-------|---------|
| BTC | `bc1qc0f5tv577z7yt59tw8sqaq3tey98xehy32frzd` |
| ETH / USDT | `0x3b7b6c47491e4778157f0756102f134d05070704` |
| SOL | `6Xuk373zc6x6XWcAAuqvbWW92zabJdCmN3CSwpsVM6sd` |
