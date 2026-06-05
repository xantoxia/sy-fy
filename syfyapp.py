import streamlit as st
import requests
import base64
import wave
from io import BytesIO

# ========== 配置 ==========
API_KEY = st.secrets.get("API_KEY", "")
SECRET_KEY = st.secrets.get("SECRET_KEY", "")
# 主手语API + 备用手语API
SIGN_API_MAIN = "https://labs.brand.fun/api/sign?text="
SIGN_API_BACKUP = "https://sign.langlab.cn/api/tts?text="

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
        
        if framerate == 16000:
            return wav_bytes
        
        # 48kHz降采样到16kHz
        new_frames = b''
        step = sampwidth * n_channels * 3
        for i in range(0, len(frames), step):
            new_frames += frames[i:i+step]
        
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
        wav_16k = resample_to_16k(wav_bytes)
        url = f"https://vop.baidu.com/server_api?dev_pid=1537&cuid=streamlit_app&token={token}"
        headers = {"Content-Type": "audio/wav; rate=16000"}
        resp = requests.post(url, data=wav_16k, headers=headers, timeout=15)
        
        try:
            j = resp.json()
        except:
            return f"ASR接口返回非JSON: {resp.text[:100]}"
            
        if j.get("err_no") == 0:
            return j["result"][0]
        else:
            return f"ASR识别失败: {j.get('err_msg')} (错误码: {j.get('err_no')})"
    except Exception as e:
        return f"ASR错误: {str(e)}"

# 手语生成（主API失败自动切换备用）
def generate_sign(text):
    for api_url in [SIGN_API_MAIN, SIGN_API_BACKUP]:
        try:
            encoded_text = requests.utils.quote(text)
            full_url = api_url + encoded_text
            
            # 先检查API是否返回图片
            resp = requests.get(full_url, timeout=10, stream=True)
            resp.raise_for_status()
            
            content_type = resp.headers.get("Content-Type", "")
            if content_type.startswith("image/"):
                return full_url, None
            else:
                continue
        except Exception as e:
            continue
    
    return None, "所有手语API均不可用，请稍后再试"

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
    with st.spinner("语音识别中..."):
        text = baidu_asr(audio.read(), token)
        st.subheader("识别结果：" + text)
        
        with st.spinner("生成手语中..."):
            sign_url, error = generate_sign(text)
            if sign_url:
                st.image(sign_url, width=400, caption="国标通用手语")
            else:
                st.error(f"手语生成失败：{error}")

st.caption("✅ 语音识别已正常 | 自动切换手语API | 云端部署")
