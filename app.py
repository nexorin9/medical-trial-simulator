"""
医疗法庭审判模拟器 - Streamlit Web 界面

用法：
    streamlit run app.py
"""

import streamlit as st
import os
import json
import time
from pathlib import Path
from datetime import datetime

# 添加项目根目录到路径
import sys
sys.path.insert(0, str(Path(__file__).parent))

from src.llm_client import create_client, LLMClient
from src.trial import TrialSession
from src.report import TrialReport
from src.data_loader import (
    load_all_sample_cases,
    list_sample_cases,
    case_to_text,
    get_normal_case,
    get_defective_case,
    get_complex_case
)

# 页面配置
st.set_page_config(
    page_title="医疗法庭审判模拟器",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="expanded"
)


def init_session_state():
    """初始化会话状态"""
    if 'trial_result' not in st.session_state:
        st.session_state.trial_result = None
    if 'trial_history' not in st.session_state:
        st.session_state.trial_history = []
    if 'api_configured' not in st.session_state:
        st.session_state.api_configured = False


def get_llm_client(provider: str, model: str, api_key: str = None) -> LLMClient:
    """创建 LLM 客户端"""
    return create_client(
        provider=provider,
        model=model,
        api_key=api_key
    )


def render_sidebar():
    """渲染侧边栏配置"""
    st.sidebar.title("⚙️ 配置")

    # API 配置
    st.sidebar.header("API 配置")

    provider = st.sidebar.selectbox(
        "选择模型提供商",
        ["openai", "anthropic"],
        format_func=lambda x: "OpenAI" if x == "openai" else "Anthropic (Claude)"
    )

    if provider == "openai":
        model = st.sidebar.selectbox(
            "选择模型",
            ["gpt-4o", "gpt-4o-mini", "gpt-4-turbo", "gpt-4"],
            index=0
        )
    else:
        model = st.sidebar.selectbox(
            "选择模型",
            [
                "claude-sonnet-4-20250514",
                "claude-3-5-sonnet-20241022",
                "claude-3-opus-20240229",
                "claude-3-haiku-20240307"
            ],
            index=1
        )

    # API Key 输入
    env_key = "OPENAI_API_KEY" if provider == "openai" else "ANTHROPIC_API_KEY"
    api_key = os.getenv(env_key)

    api_key_input = st.sidebar.text_input(
        f"API Key (可选，默认从环境变量读取)",
        type="password",
        value=api_key if api_key else "",
        help=f"如未设置环境变量 {env_key}，请在此输入"
    )

    if api_key_input:
        st.session_state.api_configured = True
    elif api_key:
        st.session_state.api_configured = True
    else:
        st.session_state.api_configured = False

    # 模型参数
    st.sidebar.header("模型参数")
    temperature = st.sidebar.slider("Temperature", 0.0, 1.0, 0.7, 0.1)
    max_tokens = st.sidebar.slider("Max Tokens", 512, 8192, 4096, 512)

    return {
        "provider": provider,
        "model": model,
        "api_key": api_key_input,
        "temperature": temperature,
        "max_tokens": max_tokens
    }


def render_medical_record_input():
    """渲染病历输入区域"""
    st.subheader("📋 病历输入")

    # 选项卡：输入方式
    tab1, tab2, tab3 = st.tabs(["✏️ 手动输入", "📁 文件上传", "📚 示例病历"])

    with tab1:
        medical_record = st.text_area(
            "请输入病历内容",
            height=300,
            placeholder="请粘贴病历内容...",
            help="直接输入或粘贴病历文本"
        )

    with tab2:
        uploaded_file = st.file_uploader(
            "上传病历文件",
            type=["txt", "json", "md"],
            help="支持 txt, json, md 格式"
        )
        if uploaded_file:
            try:
                content = uploaded_file.getvalue().decode("utf-8")
                medical_record = content
                st.success(f"已加载文件: {uploaded_file.name}")
            except Exception as e:
                st.error(f"读取文件失败: {str(e)}")
                medical_record = ""
        else:
            medical_record = ""

    with tab3:
        sample_cases = list_sample_cases()

        if sample_cases:
            case_options = {case["name"]: case for case in sample_cases}
            selected_case_name = st.selectbox(
                "选择示例病历",
                list(case_options.keys())
            )

            if selected_case_name:
                selected_case = case_options[selected_case_name]
                st.markdown(f"**类型**: {selected_case.get('type', '未知')}")
                st.markdown(f"**描述**: {selected_case.get('description', '无')}")

                # 加载完整病历
                case_data = None
                case_id = selected_case.get("id")
                if "normal" in case_id:
                    case_data = get_normal_case()
                elif "defective" in case_id:
                    case_data = get_defective_case()
                elif "complex" in case_id:
                    case_data = get_complex_case()

                if case_data:
                    medical_record = case_to_text(case_data)
                    st.text_area("病历预览", medical_record, height=200, disabled=True)
                else:
                    medical_record = ""
        else:
            st.info("暂无可用示例病历")
            medical_record = ""

    return medical_record


def render_trial_progress(phase_name: str, progress: float):
    """渲染审判进度"""
    st.progress(progress)
    st.caption(f"正在执行: {phase_name}")


def run_trial(medical_record: str, config: dict):
    """运行审判流程"""
    try:
        # 创建 LLM 客户端
        client = get_llm_client(
            provider=config["provider"],
            model=config["model"],
            api_key=config["api_key"] if config["api_key"] else None
        )

        # 创建审判会话
        trial_session = TrialSession(
            llm_client=client,
            verbose=False
        )

        # 运行完整审判
        result = trial_session.run_full_trial(medical_record)

        return result, None

    except Exception as e:
        return None, str(e)


def render_trial_result(result):
    """渲染审判结果"""
    st.success("✅ 审判完成!")

    # 创建报告生成器
    report_generator = TrialReport()

    # 获取判决摘要
    verdict = report_generator.get_verdict_summary(result)

    # 显示判决
    col1, col2 = st.columns([1, 2])

    with col1:
        st.subheader("⚖️ 审判结论")

        verdict_type = verdict.get("verdict_type", "unknown")
        verdict_label = verdict.get("verdict_label", "未知")

        if verdict_type == "qualified":
            st.success(f"**{verdict_label}**")
        elif verdict_type == "unqualified":
            st.error(f"**{verdict_label}**")
        else:
            st.warning(f"**{verdict_label}**")

        # 显示审判统计
        if result.duration_seconds:
            st.metric("耗时", f"{result.duration_seconds:.1f} 秒")

    with col2:
        st.subheader("📊 审判流程")
        phases_data = [
            ("原告指控", "⚖️"),
            ("被告辩护", "🛡️"),
            ("法官裁决", "⚖️"),
            ("陪审团意见", "👥")
        ]

        cols = st.columns(4)
        for i, (phase, icon) in enumerate(phases_data):
            with cols[i]:
                if i < len(result.phases):
                    phase_data = result.phases[i]
                    if phase_data.error:
                        st.error(f"{icon} {phase}\n❌ 失败")
                    else:
                        st.success(f"{icon} {phase}\n✅ 完成")
                else:
                    st.info(f"{icon} {phase}\n⏳ 等待")

    # 详细结果选项卡
    tab1, tab2, tab3 = st.tabs(["📝 详细报告", "🔍 阶段详情", "📋 原始数据"])

    with tab1:
        # 生成 Markdown 报告
        md_report = report_generator.generate_markdown(result)
        st.markdown(md_report)

        # 下载按钮
        col1, col2 = st.columns(2)
        with col1:
            st.download_button(
                label="📥 下载 Markdown 报告",
                data=md_report,
                file_name=f"medical_trial_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md",
                mime="text/markdown"
            )

        with col2:
            json_report = report_generator.generate_json(result)
            st.download_button(
                label="📥 下载 JSON 报告",
                data=json_report,
                file_name=f"medical_trial_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json"
            )

    with tab2:
        # 显示各阶段详细内容
        for i, phase in enumerate(result.phases):
            with st.expander(f"第{i+1}阶段: {phase.phase_name}（{phase.role}）"):
                if phase.error:
                    st.error(f"执行失败: {phase.error}")
                else:
                    st.markdown(phase.output)

    with tab3:
        # 显示原始数据
        st.json(result.to_dict())


def render_error(error_message: str):
    """渲染错误信息"""
    st.error(f"❌ 审判失败: {error_message}")
    st.info("💡 请检查:")
    st.info("- API Key 是否正确配置")
    st.info("- 网络连接是否正常")
    st.info("- 病历内容是否有效")


def main():
    """主函数"""
    init_session_state()

    # 标题
    st.title("⚖️ 医疗法庭审判模拟器")
    st.markdown("""
    用 LLM 模拟医疗事故法庭审判流程。输入病历后，AI 分别扮演：
    - **原告律师**（指控病历缺陷）
    - **被告**（病历辩护）
    - **法官**（裁决）
    - **陪审团**（综合意见）
    """)

    # 侧边栏配置
    config = render_sidebar()

    # 检查 API 配置
    if not st.session_state.api_configured:
        st.warning("⚠️ 请先在侧边栏配置 API Key")

    # 病历输入
    medical_record = render_medical_record_input()

    # 运行按钮
    st.divider()

    col1, col2 = st.columns([3, 1])
    with col1:
        run_button = st.button(
            "🚀 开始审判",
            type="primary",
            disabled=not medical_record or not st.session_state.api_configured,
            use_container_width=False
        )
    with col2:
        clear_button = st.button(
            "🗑️ 清除结果",
            use_container_width=False
        )

    if clear_button:
        st.session_state.trial_result = None
        st.rerun()

    # 执行审判
    if run_button and medical_record:
        st.divider()

        # 创建容器显示进度
        progress_container = st.container()

        with progress_container:
            st.subheader("🔄 审判进行中")

            # 阶段进度
            phase_placeholder = st.empty()
            progress_bar = st.progress(0)

            try:
                # 阶段 1
                phase_placeholder.text("⚖️ 阶段 1/4: 原告律师指控病历缺陷...")
                progress_bar.progress(25)
                time.sleep(0.5)

                # 阶段 2
                phase_placeholder.text("⚖️ 阶段 2/4: 被告辩护...")
                progress_bar.progress(50)
                time.sleep(0.5)

                # 阶段 3
                phase_placeholder.text("⚖️ 阶段 3/4: 法官裁决...")
                progress_bar.progress(75)
                time.sleep(0.5)

                # 阶段 4
                phase_placeholder.text("⚖️ 阶段 4/4: 陪审团综合意见...")
                progress_bar.progress(90)
                time.sleep(0.5)

                # 执行审判
                result, error = run_trial(medical_record, config)

                progress_bar.progress(100)
                phase_placeholder.empty()

                if error:
                    render_error(error)
                else:
                    st.session_state.trial_result = result
                    render_trial_result(result)

            except Exception as e:
                progress_bar.progress(0)
                phase_placeholder.empty()
                render_error(str(e))

    # 显示之前的结果
    elif st.session_state.trial_result:
        st.divider()
        render_trial_result(st.session_state.trial_result)


if __name__ == "__main__":
    main()
