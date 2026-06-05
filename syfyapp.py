import streamlit as st
import requests
import base64

# ========== 配置 ==========
API_KEY = st.secrets.get("API_KEY", "")
SECRET_KEY = st.secrets.get("SECRET_KEY", "")
SIGN_URL = "https://labs.brand.fun/api/sign?text="

# ========== 百度语音识别 ==========
@st.cache_resource(ttl=86400)
def get_baidu_token():
    if not API_KEY or not SECRET_KEY:
        return None
    try:
        url = f"https://aip.baidubce.com/oauth/2.0/token?grant_type=client_credentials&client_id={API_KEY}&client_secret={SECRET_KEY}"
        return requests.get(url, timeout=10).json().get("access_token")
    except:
        return None

def baidu_asr(wav_bytes, token):
    try:
        data = {
            "format": "wav", "rate": 16000, "dev_pid": 1537,
            "speech": base64.b64encode(wav_bytes).decode(),
            "len": len(wav_bytes), "access_token": token
        }
        resp = requests.post("https://aip.baidubce.com/rest/2.0/speech/v1/asr", data=data, timeout=15)
        j = resp.json()
        return j["result"][0] if j["err_no"] == 0 else f"识别失败: {j['err_msg']}"
    except Exception as e:
        return f"错误: {str(e)}"

# ========== 页面 ==========
st.set_page_config(page_title="语音转手语", layout="centered")
st.title("🗣️ 实时语音 → 国家通用手语")
st.divider()

token = get_baidu_token()
if not token:
    st.warning("请在Streamlit后台配置百度API_KEY和SECRET_KEY")
    st.stop()

# 原生录音组件（Streamlit 1.58.0 已完全修复Python3.14兼容问题）
audio = st.audio_input("点击麦克风说话", format="wav")

if audio:
    with st.spinner("识别中..."):
        text = baidu_asr(audio.read(), token)
        st.subheader("识别结果：" + text)
        try:
            st.image(SIGN_URL + requests.utils.quote(text), width=400)
        except:
            st.error("手语生成失败")

st.caption("✅ 原生Streamlit录音 | 云端部署 | 国标手语")
