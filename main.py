#!/usr/bin/env python3
"""
医疗法庭审判模拟器 - 命令行入口

用法示例：
    python main.py --input "病历内容..."
    python main.py --input data/sample_cases/defective_case.json --output report.json
    python main.py --input data/sample_cases/normal_case.json --model anthropic --model-name claude-3-5-sonnet-20241022
"""

import argparse
import sys
import os
from pathlib import Path

# 添加 src 目录到路径
sys.path.insert(0, str(Path(__file__).parent))

from src.llm_client import create_client
from src.trial import TrialSession
from src.report import TrialReport


def load_medical_record(input_path: str) -> str:
    """加载病历内容"""
    path = Path(input_path)

    if not path.exists():
        raise FileNotFoundError(f"文件不存在: {input_path}")

    # 根据文件扩展名判断加载方式
    if path.suffix.lower() == '.json':
        import json
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            # 尝试多种可能的字段名
            return data.get('content') or data.get('medical_record') or data.get('text') or json.dumps(data, ensure_ascii=False)
    else:
        # 纯文本文件
        with open(path, 'r', encoding='utf-8') as f:
            return f.read()


def main():
    parser = argparse.ArgumentParser(
        description="医疗法庭审判模拟器 - CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
    python main.py --input "患者张三，男，45岁..."
    python main.py --input data/sample_cases/defective_case.json --output report.md
    python main.py --input data/sample_cases/normal_case.json --provider anthropic
    python main.py --input "病历内容" --format markdown --output result.md
        """
    )

    # 输入选项
    parser.add_argument(
        '-i', '--input',
        required=True,
        help='病历文本或包含病历的文件路径 (.txt, .json)'
    )

    # 输出选项
    parser.add_argument(
        '-o', '--output',
        default=None,
        help='报告输出路径（默认输出到终端）'
    )

    parser.add_argument(
        '-f', '--format',
        choices=['json', 'markdown', 'md', 'text'],
        default='text',
        help='报告格式（默认: text）'
    )

    # 模型选项
    parser.add_argument(
        '-p', '--provider',
        choices=['openai', 'anthropic'],
        default='openai',
        help='LLM 提供商（默认: openai）'
    )

    parser.add_argument(
        '-m', '--model',
        default=None,
        help='模型名称（如 gpt-4o, claude-3-5-sonnet-20241022）'
    )

    parser.add_argument(
        '--api-key',
        default=None,
        help='API 密钥（也可通过环境变量 OPENAI_API_KEY 或 ANTHROPIC_API_KEY 设置）'
    )

    parser.add_argument(
        '--base-url',
        default=None,
        help='自定义 API 地址（用于代理）'
    )

    # 其他选项
    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        default=True,
        help='显示详细输出（默认: True）'
    )

    parser.add_argument(
        '-q', '--quiet',
        action='store_true',
        help='安静模式，仅显示结果'
    )

    parser.add_argument(
        '--temperature',
        type=float,
        default=0.7,
        help='LLM 温度参数（默认: 0.7）'
    )

    parser.add_argument(
        '--max-tokens',
        type=int,
        default=4096,
        help='LLM 最大 token 数（默认: 4096）'
    )

    args = parser.parse_args()

    # 安静模式时关闭详细输出
    verbose = not args.quiet

    try:
        # 1. 加载病历
        if verbose:
            print("=" * 50)
            print("医疗法庭审判模拟器")
            print("=" * 50)
            print(f"正在加载病历: {args.input}...")

        medical_record = load_medical_record(args.input)

        if verbose:
            print(f"病历加载成功，字符数: {len(medical_record)}")
            print("")

        # 2. 创建 LLM 客户端
        if verbose:
            print(f"正在初始化 {args.provider} 客户端...")

        model = args.model
        if model is None:
            if args.provider == 'openai':
                model = 'gpt-4o'
            else:
                model = 'claude-3-5-sonnet-20241022'

        client = create_client(
            provider=args.provider,
            model=model,
            api_key=args.api_key,
            base_url=args.base_url,
            temperature=args.temperature,
            max_tokens=args.max_tokens
        )

        if verbose:
            print(f"使用模型: {model}")
            print("")

        # 3. 运行审判
        if verbose:
            print("开始审判流程...")
            print("-" * 50)

        session = TrialSession(llm_client=client, verbose=verbose)
        result = session.run_full_trial(medical_record)

        if verbose:
            print("-" * 50)
            print("")

        # 4. 生成报告
        report = TrialReport()

        if args.format in ['markdown', 'md']:
            report_content = report.generate_markdown(result)
        elif args.format == 'json':
            report_content = report.generate_json(result)
        else:
            report_content = report.generate_text(result)

        # 5. 输出报告
        if args.output:
            output_path = report.export_to_file(result, args.output, args.format)
            if verbose:
                print(f"报告已保存到: {output_path}")
        else:
            print(report_content)

        # 6. 返回状态码
        if result.success:
            if verbose:
                print("")
                print("=" * 50)
                print("审判完成！")
                print("=" * 50)
            sys.exit(0)
        else:
            if verbose:
                print("")
                print("=" * 50)
                print(f"审判失败: {result.error_message}")
                print("=" * 50)
            sys.exit(1)

    except FileNotFoundError as e:
        print(f"错误: {e}", file=sys.stderr)
        sys.exit(2)
    except ValueError as e:
        print(f"配置错误: {e}", file=sys.stderr)
        sys.exit(3)
    except Exception as e:
        print(f"未知错误: {e}", file=sys.stderr)
        if verbose:
            import traceback
            traceback.print_exc()
        sys.exit(4)


if __name__ == "__main__":
    main()
