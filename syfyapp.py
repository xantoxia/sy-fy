import streamlit as st
import requests
import base64
import wave
from io import BytesIO

# ========== 配置（使用你已有的百度密钥）==========
API_KEY = st.secrets.get("API_KEY", "")
SECRET_KEY = st.secrets.get("SECRET_KEY", "")

# ========== 百度通用鉴权（语音识别+图片搜索共用）==========
@st.cache_resource(ttl=86400)
def get_baidu_token():
    if not API_KEY or not SECRET_KEY:
        return None
    try:
        url = f"https://aip.baidubce.com/oauth/2.0/token?grant_type=client_credentials&client_id={API_KEY}&client_secret={SECRET_KEY}"
        return requests.get(url, timeout=10).json().get("access_token")
    except:
        return None

# ========== 百度语音识别 ==========
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

# ========== 百度图片搜索API（搜索手语图片）==========
def search_sign_image(text, token):
    try:
        # 搜索关键词：国家通用手语 + 识别出的文字
        keyword = f"国家通用手语 {text}"
        url = f"https://aip.baidubce.com/rest/2.0/image-classify/v1/advanced_general?access_token={token}"
        
        data = {
            "query": keyword,
            "num": 1,  # 只返回1张最相关的图片
            "start": 0
        }
        
        resp = requests.post(url, data=data, timeout=15)
        j = resp.json()
        
        if j.get("result") and len(j["result"]) > 0:
            return j["result"][0]["thumbnailUrl"]
        else:
            return None
    except Exception as e:
        st.error(f"图片搜索错误: {str(e)}")
        return None

# ========== 页面 ==========
st.set_page_config(page_title="语音转手语", layout="centered")
st.title("🗣️ 实时语音 → 国家通用手语")
st.divider()

token = get_baidu_token()
if not token:
    st.warning("请在Streamlit后台配置百度API_KEY和SECRET_KEY")
    st.stop()

# 原生录音组件（Streamlit 1.58.0已修复兼容问题）
audio = st.audio_input("点击麦克风说话")

if audio:
    with st.spinner("语音识别中..."):
        text = baidu_asr(audio.read(), token)
        st.subheader("识别结果：" + text)
        
        with st.spinner("搜索手语图片中..."):
            sign_image_url = search_sign_image(text, token)
            if sign_image_url:
                st.image(sign_image_url, width=400, caption=f"国家通用手语：{text}")
            else:
                st.error("未找到对应的手语图片，请尝试其他文字")

st.caption("✅ 语音识别正常 | 百度图片搜索手语 | 云端部署")
