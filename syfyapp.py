import streamlit as st
import requests
import base64
import wave
from io import BytesIO

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

# 音频重采样：48kHz → 16kHz（百度ASR要求）
def resample_to_16k(wav_bytes):
    try:
        with wave.open(BytesIO(wav_bytes), 'rb') as wf:
            n_channels = wf.getnchannels()
            sampwidth = wf.getsampwidth()
            framerate = wf.getframerate()
            n_frames = wf.getnframes()
            frames = wf.readframes(n_frames)
        
        # 如果已经是16kHz，直接返回
        if framerate == 16000:
            return wav_bytes
        
        # 简单降采样：每3个样本取1个（48000/16000=3）
        new_frames = b''
        for i in range(0, len(frames), sampwidth * n_channels * 3):
            new_frames += frames[i:i+sampwidth*n_channels]
        
        # 生成新的WAV文件
        output = BytesIO()
        with wave.open(output, 'wb') as wf:
            wf.setnchannels(n_channels)
            wf.setsampwidth(sampwidth)
            wf.setframerate(16000)
            wf.writeframes(new_frames)
        
        return output.getvalue()
    except:
        return wav_bytes

def baidu_asr(wav_bytes, token):
    try:
        # 重采样到16kHz
        wav_16k = resample_to_16k(wav_bytes)
        
        # 更新为百度最新接口地址
        url = f"https://vop.baidu.com/server_api?dev_pid=1537&cuid=streamlit_app&token={token}"
        
        headers = {"Content-Type": "audio/wav; rate=16000"}
        
        resp = requests.post(url, data=wav_16k, headers=headers, timeout=15)
        
        try:
            j = resp.json()
        except:
            return f"接口返回非JSON: {resp.text[:100]}"
            
        if j.get("err_no") == 0:
            return j["result"][0]
        else:
            return f"识别失败: {j.get('err_msg')} (错误码: {j.get('err_no')})"
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

# 原生录音组件
audio = st.audio_input("点击麦克风说话")

if audio:
    with st.spinner("识别中..."):
        text = baidu_asr(audio.read(), token)
        st.subheader("识别结果：" + text)
        try:
            st.image(SIGN_URL + requests.utils.quote(text), width=400)
        except:
            st.error("手语生成失败")

st.caption("✅ 原生Streamlit录音 | 自动重采样 | 云端部署 | 国标手语")
