"""
命令行主程序

提供命令行交互接口
"""

import argparse
import json
import sys
import os
from typing import Dict, Any, Optional, List
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.prompts.base import TrialContext
from src.trial.controller import TrialController
from src.clients.config import load_config, get_client, validate_environment
from src.utils.logging_config import setup_logging, get_logger, TrialLogger
from src.utils.exceptions import setup_global_exception_handler, ConfigurationError
from .output import OutputFormatter

# 初始化日志和全局异常处理
_logger = get_logger("medical_trial")


def parse_args():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(
        description="医保费用审判模拟器 - 用LLM模拟医保审核官'审判'每笔费用",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例用法:
  # 交互式模式
  python -m src.cli.main

  # 从文件加载审判
  python -m src.cli.main --expenses data/sample_expenses.json --diffs data/sample_diffs.json

  # 指定输出格式
  python -m src.cli.main --expenses data/sample_expenses.json --output result.json --format json

  # 使用特定 LLM 提供商
  python -m src.cli.main --expenses data/sample_expenses.json --provider openai

  # 批量处理
  python -m src.cli.main --batch --expenses-dir ./data/expenses/
        """
    )

    # 基础参数
    parser.add_argument(
        "--expenses", "-e",
        help="费用明细 JSON 文件路径"
    )
    parser.add_argument(
        "--diffs", "-d",
        help="结算差异 JSON 文件路径"
    )
    parser.add_argument(
        "--catalog", "-c",
        help="医保目录 JSON 文件路径"
    )
    parser.add_argument(
        "--case-id",
        help="案件编号（可选）"
    )

    # 输出参数
    parser.add_argument(
        "--output", "-o",
        help="输出文件路径（可选，默认输出到终端）"
    )
    parser.add_argument(
        "--format", "-f",
        choices=["json", "text", "markdown", "html"],
        default="text",
        help="输出格式（默认: text）"
    )

    # LLM 参数
    parser.add_argument(
        "--provider", "-p",
        choices=["anthropic", "openai"],
        help="LLM 提供商（默认从环境变量读取）"
    )
    parser.add_argument(
        "--model", "-m",
        help="模型名称"
    )
    parser.add_argument(
        "--mock",
        action="store_true",
        help="使用模拟响应（无需 API key）"
    )

    # 批量处理
    parser.add_argument(
        "--batch",
        action="store_true",
        help="批量处理模式"
    )
    parser.add_argument(
        "--expenses-dir",
        help="批量处理时的费用文件目录"
    )

    # 日志参数
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="显示详细输出"
    )
    parser.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        default="INFO",
        help="日志级别（默认: INFO）"
    )
    parser.add_argument(
        "--log-file",
        help="日志文件路径"
    )

    # 其他
    parser.add_argument(
        "--interactive", "-i",
        action="store_true",
        help="交互式模式"
    )

    return parser.parse_args()


def load_json_file(file_path: str) -> Any:
    """加载 JSON 文件"""
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"文件不存在: {file_path}")

    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)


def create_context_from_args(args) -> Optional[TrialContext]:
    """从命令行参数创建审判上下文"""
    context = TrialContext()

    # 加载费用明细
    if args.expenses:
        expenses = load_json_file(args.expenses)
        if isinstance(expenses, list):
            context.expense_items = expenses
        elif isinstance(expenses, dict) and "items" in expenses:
            context.expense_items = expenses["items"]

    # 加载结算差异
    if args.diffs:
        diffs = load_json_file(args.diffs)
        if isinstance(diffs, list):
            context.diff_items = diffs
        elif isinstance(diffs, dict) and "items" in diffs:
            context.diff_items = diffs["items"]

    # 加载医保目录
    if args.catalog:
        catalog = load_json_file(args.catalog)
        context.medicare_catalog = catalog

    # 如果没有加载到数据，询问用户
    if not context.expense_items and not context.diff_items:
        return None

    return context


def print_progress(message: str, phase):
    """打印进度信息"""
    phase_names = {
        "prosecutor": "起诉阶段",
        "defense": "辩护阶段",
        "judge": "裁决阶段",
        "completed": "完成",
        "initial": "初始化",
    }
    print(f"  [{phase_names.get(phase.value, phase.value)}] {message}")


def run_single(
    expenses: Optional[List[Dict]] = None,
    diffs: Optional[List[Dict]] = None,
    catalog: Optional[Dict] = None,
    case_id: Optional[str] = None,
    provider: Optional[str] = None,
    model: Optional[str] = None,
    mock: bool = False,
    output_format: str = "text",
    output_file: Optional[str] = None,
    verbose: bool = False,
) -> Dict[str, Any]:
    """
    运行单次审判

    Args:
        expenses: 费用明细列表
        diffs: 结算差异列表
        catalog: 医保目录
        case_id: 案件编号
        provider: LLM 提供商
        model: 模型名称
        mock: 是否使用模拟响应
        output_format: 输出格式
        output_file: 输出文件路径
        verbose: 是否显示详细输出

    Returns:
        审判结果
    """
    # 创建审判上下文
    context = TrialContext()
    context.expense_items = expenses or []
    context.diff_items = diffs or []
    context.medicare_catalog = catalog or {}

    # 创建日志记录器
    trial_logger = TrialLogger()
    if case_id:
        trial_logger.set_case_id(case_id)

    # 记录开始
    _logger.info(f"开始审判 - 费用条目: {len(expenses or [])}, 差异条目: {len(diffs or [])}")

    # 创建 LLM 客户端（如果需要）
    llm_client = None
    if not mock:
        try:
            env_status = validate_environment()
            if env_status.get("any_provider_available"):
                llm_client = get_client(provider=provider, model=model)
                if verbose:
                    print(f"使用 LLM 提供商: {provider or 'auto'}")
                _logger.info(f"LLM 客户端创建成功 - 提供商: {provider or 'auto'}")
            else:
                print("警告: 未检测到 API key，将使用模拟响应")
                _logger.warning("未检测到 API key，使用模拟响应模式")
                mock = True
        except Exception as e:
            print(f"警告: 无法创建 LLM 客户端: {e}，将使用模拟响应")
            _logger.warning(f"LLM 客户端创建失败: {e}，使用模拟响应模式")
            mock = True
    else:
        if verbose:
            print("使用模拟响应模式")
        _logger.info("使用模拟响应模式")

    # 创建审判控制器
    callback = print_progress if verbose else None
    controller = TrialController(llm_client=llm_client, callback=callback)

    # 运行审判
    print("\n" + "=" * 50)
    print("       医保费用审判模拟器 - 开始审判")
    print("=" * 50 + "\n")

    result = controller.run_trial(context, case_id=case_id)

    # 记录审判结果
    _logger.info(f"审判完成 - 状态: {result.status}, 裁决: {result.final_verdict}")
    if result.status == "error":
        _logger.error(f"审判出错 - 案件: {case_id}")

    # 格式化输出
    result_dict = result.to_dict()

    if output_format == "json":
        output = OutputFormatter.format_json(result_dict)
    elif output_format == "markdown":
        output = OutputFormatter.format_markdown(result_dict)
    elif output_format == "html":
        output = OutputFormatter.format_html(result_dict)
    else:
        output = OutputFormatter.format_text(result_dict)

    # 输出结果
    if output_file:
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(output)
        print(f"\n结果已保存到: {output_file}")
    else:
        print("\n" + output)

    return result_dict


def run_batch(
    expenses_dir: Optional[str] = None,
    provider: Optional[str] = None,
    model: Optional[str] = None,
    mock: bool = False,
    output_format: str = "text",
    output_file: Optional[str] = None,
    verbose: bool = False,
):
    """
    运行批量审判

    Args:
        expenses_dir: 费用文件目录
        provider: LLM 提供商
        model: 模型名称
        mock: 是否使用模拟响应
        output_format: 输出格式
        output_file: 输出文件路径
        verbose: 是否显示详细输出
    """
    import time

    # 收集费用文件
    expense_files = []
    if expenses_dir and os.path.isdir(expenses_dir):
        for f in os.listdir(expenses_dir):
            if f.endswith('.json'):
                expense_files.append(os.path.join(expenses_dir, f))
    else:
        # 使用默认示例数据作为批量测试
        print("未指定费用目录或目录不存在，使用内置示例数据进行批量测试...")
        expense_files = ["sample_1.json", "sample_2.json", "sample_3.json"]

    total = len(expense_files)
    if total == 0:
        print("未找到费用文件")
        return

    print("\n" + "=" * 60)
    print(f"       医保费用审判模拟器 - 批量审判 ({total} 个案件)")
    print("=" * 60 + "\n")

    # 创建 LLM 客户端
    llm_client = None
    if not mock:
        try:
            env_status = validate_environment()
            if env_status.get("any_provider_available"):
                llm_client = get_client(provider=provider, model=model)
                if verbose:
                    print(f"使用 LLM 提供商: {provider or 'auto'}")
            else:
                print("警告: 未检测到 API key，将使用模拟响应")
                mock = True
        except Exception as e:
            print(f"警告: 无法创建 LLM 客户端: {e}，将使用模拟响应")
            mock = True
    else:
        if verbose:
            print("使用模拟响应模式")

    # 创建审判控制器
    callback = print_progress if verbose else None
    controller = TrialController(llm_client=llm_client, callback=callback)

    # 示例数据模板
    sample_expenses = [
        [
            {"item_code": "250301003", "item_name": "血清肌酸激酶测定", "quantity": 1, "unit_price": 60.0, "total_amount": 60.0, "expense_type": "检验费"},
            {"item_code": "110200001", "item_name": "普通门诊诊查费", "quantity": 1, "unit_price": 10.0, "total_amount": 10.0, "expense_type": "诊查费"},
            {"item_code": "120100003", "item_name": "一级护理", "quantity": 3, "unit_price": 60.0, "total_amount": 180.0, "expense_type": "护理费"}
        ],
        [
            {"item_code": "250403019", "item_name": "乙型肝炎表面抗体测定", "quantity": 1, "unit_price": 30.0, "total_amount": 30.0, "expense_type": "检验费"},
            {"item_code": "310300008", "item_name": "眼压测定", "quantity": 2, "unit_price": 25.0, "total_amount": 50.0, "expense_type": "检查费"}
        ],
        [
            {"item_code": "110100001", "item_name": "挂号费", "quantity": 1, "unit_price": 1.0, "total_amount": 1.0, "expense_type": "挂号费"},
            {"item_code": "250101008", "item_name": "血常规检查", "quantity": 1, "unit_price": 25.0, "total_amount": 25.0, "expense_type": "检验费"},
            {"item_code": "310500001", "item_name": "换药", "quantity": 5, "unit_price": 20.0, "total_amount": 100.0, "expense_type": "治疗费"}
        ]
    ]

    sample_diffs = [
        [
            {"diff_type": "超标准收费", "diff_reason": "护理费超标准", "hospital_declared_amount": 180.0, "medicare_calculated_amount": 150.0, "diff_amount": 30.0, "severity": "中等", "description": "一级护理收费超标准"},
            {"diff_type": "目录匹配", "diff_reason": "检验项目编码不匹配", "hospital_declared_amount": 60.0, "medicare_calculated_amount": 50.0, "diff_amount": 10.0, "severity": "低", "description": "血清肌酸激酶测定编码调整"}
        ],
        [
            {"diff_type": "项目重复", "diff_reason": "眼压测定重复计费", "hospital_declared_amount": 50.0, "medicare_calculated_amount": 25.0, "diff_amount": 25.0, "severity": "高", "description": "眼压测定重复收费"}
        ],
        [
            {"diff_type": "超范围用药", "diff_reason": "超出医保目录适应症", "hospital_declared_amount": 100.0, "medicare_calculated_amount": 60.0, "diff_amount": 40.0, "severity": "高", "description": "换药费用超范围"}
        ]
    ]

    # 创建上下文列表
    contexts = []
    for i in range(min(total, 3)):
        context = TrialContext()
        context.expense_items = sample_expenses[i] if i < len(sample_expenses) else sample_expenses[0]
        context.diff_items = sample_diffs[i] if i < len(sample_diffs) else sample_diffs[0]
        contexts.append(context)

    # 运行批量审判
    results = []
    start_time = time.time()

    for i, context in enumerate(contexts):
        case_id = f"case_{i+1}"
        print(f"\n[{i+1}/{total}] 正在审判案件: {case_id}...")

        try:
            result = controller.run_trial(context, case_id=case_id)
            results.append(result)

            # 显示进度
            progress = (i + 1) / total * 100
            print(f"  进度: {progress:.0f}% ({i+1}/{total}) - 状态: {result.status}")

            if verbose and result.final_verdict:
                print(f"  裁决: {result.final_verdict}")

        except Exception as e:
            print(f"  错误: {e}")
            # 创建错误结果
            from src.trial.controller import TrialResult
            error_result = TrialResult(
                case_id=case_id,
                start_time=time.strftime("%Y-%m-%dT%H:%M:%S"),
                end_time=time.strftime("%Y-%m-%dT%H:%M:%S"),
                status="error",
            )
            results.append(error_result)

    end_time = time.time()
    elapsed = end_time - start_time

    # 生成汇总统计
    summary = controller.generate_trial_summary(results)

    # 显示汇总结果
    print("\n" + "=" * 60)
    print("                    批量审判汇总")
    print("=" * 60)
    print(f"\n总案件数: {summary['total_cases']}")
    print(f"完成: {summary['completed_cases']}")
    print(f"失败: {summary['error_cases']}")
    print(f"指控总金额: ¥{summary['total_accused_amount']:.2f}")
    print(f"核减总金额: ¥{summary['total_ruling_amount']:.2f}")
    print(f"\n裁决分布:")
    for verdict, count in summary['verdict_distribution'].items():
        print(f"  - {verdict}: {count}")
    print(f"\n耗时: {elapsed:.2f} 秒")

    # 输出结果
    output_data = {
        "summary": summary,
        "results": [r.to_dict() for r in results],
    }

    if output_format == "json":
        output = json.dumps(output_data, ensure_ascii=False, indent=2)
    elif output_format == "markdown":
        output = f"# 批量审判汇总\n\n" + OutputFormatter.format_batch_summary(summary) + "\n\n" + \
                 "## 案件详情\n\n" + \
                 "\n\n".join([OutputFormatter.format_markdown(r) for r in output_data["results"]])
    elif output_format == "html":
        output = OutputFormatter.format_html(output_data)
    else:
        # 文本格式只显示汇总
        output = OutputFormatter.format_batch_summary(summary)

    if output_file:
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(output)
        print(f"\n结果已保存到: {output_file}")
    else:
        print("\n" + output)


def run_interactive():
    """交互式模式"""
    print("\n" + "=" * 60)
    print("      医保费用审判模拟器 - 交互式模式")
    print("=" * 60)
    print()
    print("本程序将引导您完成医保费用的审判流程")
    print()

    # 选择模式
    print("请选择输入方式:")
    print("  1. 从文件加载数据")
    print("  2. 手动输入数据")
    print("  3. 使用内置示例数据")
    print()

    choice = input("请选择 (1/2/3): ").strip()

    expenses = None
    diffs = None
    catalog = None
    case_id = None

    if choice == "1":
        # 从文件加载
        expenses_file = input("费用明细文件路径: ").strip()
        diffs_file = input("结算差异文件路径（可选，回车跳过）: ").strip()
        catalog_file = input("医保目录文件路径（可选，回车跳过）: ").strip()

        try:
            expenses = load_json_file(expenses_file)
            if isinstance(expenses, list):
                expenses = expenses
            elif isinstance(expenses, dict) and "items" in expenses:
                expenses = expenses["items"]

            if diffs_file:
                diffs = load_json_file(diffs_file)
                if isinstance(diffs, list):
                    diffs = diffs
                elif isinstance(diffs, dict) and "items" in diffs:
                    diffs = diffs["items"]

            if catalog_file:
                catalog = load_json_file(catalog_file)
        except Exception as e:
            print(f"错误: {e}")
            return

    elif choice == "2":
        # 手动输入
        print("\n请输入费用明细（JSON 格式，回车完成输入）:")
        print("示例: [{\"item_name\": \"检查费\", \"total_amount\": 100}]")
        expenses_input = input()
        try:
            expenses = json.loads(expenses_input) if expenses_input else []
        except json.JSONDecodeError:
            print("JSON 格式错误，将使用空列表")
            expenses = []

        print("\n请输入结算差异（JSON 格式，回车完成输入）:")
        diffs_input = input()
        try:
            diffs = json.loads(diffs_input) if diffs_input else []
        except json.JSONDecodeError:
            print("JSON 格式错误，将使用空列表")
            diffs = []

    elif choice == "3":
        # 使用示例数据
        print("使用内置示例数据...")
        # 模拟一些示例数据
        expenses = [
            {
                "item_code": "250301003",
                "item_name": "血清肌酸激酶测定",
                "quantity": 1,
                "unit_price": 60.0,
                "total_amount": 60.0,
                "expense_type": "检验费"
            },
            {
                "item_code": "110200001",
                "item_name": "普通门诊诊查费",
                "quantity": 1,
                "unit_price": 10.0,
                "total_amount": 10.0,
                "expense_type": "诊查费"
            },
            {
                "item_code": "120100003",
                "item_name": "一级护理",
                "quantity": 3,
                "unit_price": 60.0,
                "total_amount": 180.0,
                "expense_type": "护理费"
            }
        ]

        diffs = [
            {
                "diff_type": "超标准收费",
                "diff_reason": "护理费超标准",
                "hospital_declared_amount": 180.0,
                "medicare_calculated_amount": 150.0,
                "diff_amount": 30.0,
                "severity": "中等",
                "description": "一级护理收费超标准"
            },
            {
                "diff_type": "目录匹配",
                "diff_reason": "检验项目编码不匹配",
                "hospital_declared_amount": 60.0,
                "medicare_calculated_amount": 50.0,
                "diff_amount": 10.0,
                "severity": "低",
                "description": "血清肌酸激酶测定编码调整"
            }
        ]

    else:
        print("无效选择")
        return

    # 选择输出格式
    print("\n请选择输出格式:")
    print("  1. 文本 (text)")
    print("  2. JSON (json)")
    print("  3. Markdown (markdown)")
    print("  4. HTML (html)")
    print()

    format_choice = input("请选择 (1/2/3/4): ").strip()
    format_map = {"1": "text", "2": "json", "3": "markdown", "4": "html"}
    output_format = format_map.get(format_choice, "text")

    # 是否使用模拟
    env_status = validate_environment()
    use_mock = not env_status.get("any_provider_available", False)

    if not use_mock:
        mock_choice = input("\n是否使用模拟响应？(y/N): ").strip().lower()
        use_mock = mock_choice == "y"

    # 运行审判
    result = run_single(
        expenses=expenses,
        diffs=diffs,
        catalog=catalog,
        case_id=case_id,
        mock=use_mock,
        output_format=output_format,
    )


def main():
    """主函数"""
    args = parse_args()

    # 初始化日志系统
    setup_logging(
        level=args.log_level,
        log_file=args.log_file,
        verbose=args.verbose,
    )

    # 设置全局异常处理器
    error_log_file = getattr(args, 'log_file', None)
    if error_log_file:
        error_log_path = str(Path(error_log_file).parent / "errors.log")
        setup_global_exception_handler(log_file=error_log_path, reraise=False)
    else:
        setup_global_exception_handler(reraise=False)

    _logger.info("医保费用审判模拟器启动")

    # 交互式模式（仅当没有其他参数时）
    if args.interactive:
        run_interactive()
        return

    # 批量处理模式
    if args.batch:
        run_batch(
            expenses_dir=args.expenses_dir,
            provider=args.provider,
            model=args.model,
            mock=args.mock,
            output_format=args.format,
            output_file=args.output,
            verbose=args.verbose,
        )
        return

    # 单次审判模式（从文件加载）
    if args.expenses:
        try:
            context = create_context_from_args(args)

            if context is None:
                print("错误: 无法加载费用明细数据")
                return

            run_single(
                expenses=context.expense_items,
                diffs=context.diff_items,
                catalog=context.medicare_catalog,
                case_id=args.case_id,
                provider=args.provider,
                model=args.model,
                mock=args.mock,
                output_format=args.format,
                output_file=args.output,
                verbose=args.verbose,
            )

        except Exception as e:
            print(f"错误: {e}")
            if args.verbose:
                import traceback
                traceback.print_exc()
            sys.exit(1)
        return

    # Mock 模式（使用内置示例数据）
    if args.mock:
        print("使用内置示例数据进行模拟审判...")
        # 示例数据
        expenses = [
            {
                "item_code": "250301003",
                "item_name": "血清肌酸激酶测定",
                "quantity": 1,
                "unit_price": 60.0,
                "total_amount": 60.0,
                "expense_type": "检验费"
            },
            {
                "item_code": "110200001",
                "item_name": "普通门诊诊查费",
                "quantity": 1,
                "unit_price": 10.0,
                "total_amount": 10.0,
                "expense_type": "诊查费"
            },
            {
                "item_code": "120100003",
                "item_name": "一级护理",
                "quantity": 3,
                "unit_price": 60.0,
                "total_amount": 180.0,
                "expense_type": "护理费"
            }
        ]

        diffs = [
            {
                "diff_type": "超标准收费",
                "diff_reason": "护理费超标准",
                "hospital_declared_amount": 180.0,
                "medicare_calculated_amount": 150.0,
                "diff_amount": 30.0,
                "severity": "中等",
                "description": "一级护理收费超标准"
            },
            {
                "diff_type": "目录匹配",
                "diff_reason": "检验项目编码不匹配",
                "hospital_declared_amount": 60.0,
                "medicare_calculated_amount": 50.0,
                "diff_amount": 10.0,
                "severity": "低",
                "description": "血清肌酸激酶测定编码调整"
            }
        ]

        run_single(
            expenses=expenses,
            diffs=diffs,
            case_id=args.case_id,
            mock=True,
            output_format=args.format,
            output_file=args.output,
            verbose=args.verbose,
        )
        return

    # 默认进入交互式模式
    run_interactive()


if __name__ == "__main__":
    main()
