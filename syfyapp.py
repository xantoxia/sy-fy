import streamlit as st
import requests
import base64

# ========== 从 Streamlit 云端安全读取密钥 ==========
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
        res = requests.get(url, timeout=10)
        return res.json().get("access_token")
    except Exception as e:
        st.error(f"获取Token失败: {str(e)}")
        return None

def baidu_asr(wav_bytes, token):
    try:
        speech = base64.b64encode(wav_bytes).decode()
        data = {
            "format": "wav",
            "rate": 16000,
            "dev_pid": 1537,
            "speech": speech,
            "len": len(wav_bytes),
            "access_token": token
        }
        resp = requests.post("https://aip.baidubce.com/rest/2.0/speech/v1/asr", data=data, timeout=15)
        j = resp.json()
        if j.get("err_no") == 0:
            return j["result"][0]
        return f"识别失败 ({j.get('err_msg')})"
    except Exception as e:
        return f"识别错误: {str(e)}"

# ========== 页面 ==========
st.set_page_config(page_title="语音转手语", layout="centered")
st.title("🗣️ 实时语音 → 国家通用手语")
st.divider()

token = get_baidu_token()

# 修复：使用正式版 st.audio_input
audio_value = st.audio_input("点击麦克风说话", format="wav")

if audio_value and token:
    bytes_data = audio_value.read()
    with st.spinner("识别中..."):
        text = baidu_asr(bytes_data, token)
        st.subheader("识别结果：" + text)

        try:
            sign_url = SIGN_URL + requests.utils.quote(text)
            st.image(sign_url, width=400)
        except Exception as e:
            st.error(f"手语生成失败: {str(e)}")

if not token:
    st.warning("请在 Streamlit 后台配置百度 API_KEY 和 SECRET_KEY")

st.caption("✅ 安全无密钥泄露｜云端部署｜国标手语")
