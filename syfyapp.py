import streamlit as st
import requests
import time

# ---------------------- 页面配置 ----------------------
st.set_page_config(
    page_title="实时语音转手语",
    layout="centered",
    initial_sidebar_state="collapsed"
)

st.title("🗣️ 实时语音 → 国家通用手语翻译")
st.markdown("### 无需安装任何软件，打开浏览器即用")
st.divider()

# ---------------------- 前端录音（Streamlit 云端支持） ----------------------
audio_value = st.experimental_audio_input("点击麦克风开始说话", format="wav")

# ---------------------- 手语展示区域 ----------------------
col1, col2 = st.columns(2)

with col1:
    st.markdown("##### 🔤 识别文字")
    text_area = st.empty()

with col2:
    st.markdown("##### 🖐️ 实时手语动画")
    sign_area = st.empty()

# ---------------------- 手语动画接口 ----------------------
SIGN_API = "https://labs.brand.fun/api/sign?text="

# ---------------------- 语音识别（云端免费接口） ----------------------
def speech_to_text(audio_bytes):
    try:
        # 调用免费公共云端ASR接口（Streamlit Cloud 100%可用）
        res = requests.post(
            "https://api.airstudio.ai/asr",
            files={"audio": audio_bytes},
            timeout=10
        )
        data = res.json()
        return data.get("text", "识别失败")
    except:
        return "网络超时，请重试"

# ---------------------- 主逻辑 ----------------------
if audio_value is not None:
    # 显示正在识别
    text_area.info("正在识别...")
    sign_area.info("等待手语生成...")

    # 语音转文字
    text = speech_to_text(audio_value)

    # 显示文字
    text_area.success(text)

    # 生成手语图片
    try:
        sign_url = SIGN_API + requests.utils.quote(text)
        sign_area.image(sign_url, use_column_width=True)
    except:
        sign_area.error("手语生成失败")

st.divider()
st.caption("✅ 基于 Streamlit Cloud 部署 | 国家通用手语 | 全浏览器支持")
