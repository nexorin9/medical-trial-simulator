# Medical Trial Simulator

Simulates medical malpractice court trial processes using LLM. After inputting a medical record, AI plays the roles of plaintiff (accusing record defects), defendant (record defense), judge (ruling), and jury (comprehensive opinion) to generate trial records and multi-dimensional quality assessment reports.

## Features

- **AI Role-Playing**: Four-way confrontation between plaintiff lawyer, defendant (medical record), judge, and jury
- **Multi-dimensional Evaluation**: Completeness, logical consistency, standard compliance, evidence support, timeline accuracy
- **Dual Modes**: Web interface (Streamlit) and command-line interface
- **Flexible Configuration**: Supports OpenAI and Anthropic APIs

## Quick Start

### Installation

```bash
pip install -r requirements.txt
```

### Configure API Key

Create a `.env` file:

```bash
# Choose one
OPENAI_API_KEY=your_openai_key
ANTHROPIC_API_KEY=your_anthropic_key
```

Or use `.env.example` as reference.

### Running

**Web Interface:**
```bash
streamlit run app.py
```

**Command Line:**
```bash
python main.py --input "medical record content..." --output report.json
```

## Project Structure

```
medical-trial-simulator/
├── app.py              # Streamlit Web application
├── main.py             # CLI entry point
├── requirements.txt    # Dependencies
├── .gitignore          # Git ignore configuration
├── README.md           # This file
├── buymeacoffee.png    # Donation image
├── src/
│   ├── llm_client.py   # LLM client wrapper
│   ├── prompts.py      # Role prompt templates
│   ├── trial.py        # Trial process logic
│   ├── evaluator.py    # Medical record evaluator
│   └── report.py       # Report generator
├── data/
│   └── sample_cases/   # Sample medical records
└── tests/              # Unit tests
```

## Usage Examples

### Web Interface

1. Run `streamlit run app.py`
2. Configure API Key on the left sidebar
3. Input or select a sample medical record
4. Click "Start Trial" button
5. View trial process and assessment report

### Command Line

```bash
# Input medical record from file
python main.py --input data/sample_cases/case1.txt --output report.json

# Input medical record directly
python main.py --input "Patient complaint: ..." --model gpt-4o
```

## Evaluation Dimensions

| Dimension | Description |
|-----------|-------------|
| Completeness | Whether the medical record contains necessary information items |
| Logical Consistency | Whether there are logical contradictions in diagnosis, treatment, medication, etc. |
| Standard Compliance | Whether it complies with medical documentation standards |
| Evidence Support | Whether diagnostic and treatment measures have corresponding record support |
| Timeline Accuracy | Whether time records are accurate and continuous |

## Tech Stack

- **Python 3.10+**
- **Streamlit** - Web interface
- **OpenAI / Anthropic** - LLM capabilities

## License

MIT License
