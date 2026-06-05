import streamlit as st
import requests

# ---------------------- 页面配置 ----------------------
st.set_page_config(
    page_title="实时语音转手语",
    layout="centered"
)

st.title("🗣️ 实时语音 → 国家通用手语")
st.divider()

# ---------------------- 录音 ----------------------
audio = st.audio_input("点击麦克风说话")
text_out = st.empty()
sign_out = st.empty()

# ---------------------- 手语接口 ----------------------
SIGN_URL = "https://labs.brand.fun/api/sign?text="

# ---------------------- 免费在线语音识别 ----------------------
def asr(audio_bytes):
    try:
        r = requests.post(
            "https://api.airstudio.ai/asr",
            files={"audio": audio_bytes},
            timeout=8
        )
        return r.json().get("text", "识别失败")
    except:
        return "网络超时"

# ---------------------- 执行 ----------------------
if audio:
    with st.spinner("识别中..."):
        text = asr(audio)
        text_out.subheader("识别结果：" + text)
        
        try:
            sign_out.image(SIGN_URL + requests.utils.quote(text))
        except:
            sign_out.error("手语生成失败")

st.caption("✅ 任何电脑打开即用 | 云端运行 | 无需安装")
