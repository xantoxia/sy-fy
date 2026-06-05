import streamlit as st
import requests
import base64
import wave
from io import BytesIO

# ========== 配置 ==========
# 百度语音识别密钥（你已有的）
BAIDU_API_KEY = st.secrets.get("API_KEY", "")
BAIDU_SECRET_KEY = st.secrets.get("SECRET_KEY", "")

# 果不其然开放平台手语合成密钥
GBQR_API_KEY = st.secrets.get("GBQR_API_KEY", "")
GBQR_API_SECRET = st.secrets.get("GBQR_API_SECRET", "")

# ========== 百度语音识别 ==========
@st.cache_resource(ttl=86400)
def get_baidu_token():
    if not BAIDU_API_KEY or not BAIDU_SECRET_KEY:
        return None
    try:
        url = f"https://aip.baidubce.com/oauth/2.0/token?grant_type=client_credentials&client_id={BAIDU_API_KEY}&client_secret={BAIDU_SECRET_KEY}"
        return requests.get(url, timeout=10).json().get("access_token")
    except:
        return None

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

# ========== 果不其然开放平台 长句手语合成（个人免费）==========
def generate_sign_video_gbqr(text):
    try:
        # 果不其然官方API端点
        url = "https://cloud.gbqr.net/api/v1/sign-language/generate"
        
        headers = {
            "Content-Type": "application/json",
            "X-API-Key": GBQR_API_KEY,
            "X-API-Secret": GBQR_API_SECRET
        }
        
        data = {
            "text": text,
            "avatar": "female_1",  # 虚拟人形象：female_1/male_1
            "background": "white",  # 背景颜色：white/green/blue
            "format": "mp4",        # 输出格式：mp4/gif
            "speed": 1.0            # 播放速度：0.5-2.0
        }
        
        resp = requests.post(url, json=data, headers=headers, timeout=30)
        j = resp.json()
        
        if j.get("code") == 0:
            return j["data"]["video_url"], None
        else:
            return None, f"手语合成失败: {j.get('msg')} (错误码: {j.get('code')})"
    except Exception as e:
        return None, f"手语合成错误: {str(e)}"

# ========== 页面 ==========
st.set_page_config(page_title="语音转手语", layout="centered")
st.title("🗣️ 实时语音 → 国家通用手语动画")
st.divider()

# 检查密钥配置
baidu_token = get_baidu_token()
if not baidu_token:
    st.warning("请在Streamlit后台配置百度API_KEY和SECRET_KEY")
    st.stop()

if not GBQR_API_KEY or not GBQR_API_SECRET:
    st.warning("请在Streamlit后台配置果不其然GBQR_API_KEY和GBQR_API_SECRET")
    st.stop()

# 原生录音组件
audio = st.audio_input("点击麦克风说话")

if audio:
    with st.spinner("语音识别中..."):
        text = baidu_asr(audio.read(), baidu_token)
        st.subheader("识别结果：" + text)
        
        with st.spinner("生成手语动画中..."):
            video_url, error = generate_sign_video_gbqr(text)
            if video_url:
                st.video(video_url, format="video/mp4", start_time=0, autoplay=True, loop=True)
            else:
                st.error(error)

st.caption("✅ 百度语音识别 | 果不其然长句手语合成 | 国家通用手语标准")
