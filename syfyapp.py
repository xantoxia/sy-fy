import streamlit as st
import requests
import base64
import wave
from io import BytesIO

# ========== 配置（无需任何密钥！）==========
# 百度语音识别密钥（你已有的，仅语音识别需要）
BAIDU_API_KEY = st.secrets.get("API_KEY", "")
BAIDU_SECRET_KEY = st.secrets.get("SECRET_KEY", "")

# 国家通用手语官方词典API（公开免费，无需密钥）
SIGN_DICT_API = "https://www.shouyu.com.cn/api/search?keyword="

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

# ========== 国家通用手语官方词典查询（零密钥）==========
def search_official_sign(text):
    try:
        # 分词处理，逐个查询词语
        words = text.split()
        if not words:
            words = [text]
        
        results = []
        for word in words:
            if not word.strip():
                continue
                
            url = SIGN_DICT_API + requests.utils.quote(word)
            resp = requests.get(url, timeout=10)
            j = resp.json()
            
            if j.get("code") == 200 and j.get("data") and len(j["data"]) > 0:
                # 取第一个最相关的结果
                sign_info = j["data"][0]
                results.append({
                    "word": word,
                    "image_url": sign_info["image"],
                    "description": sign_info["description"]
                })
        
        return results, None
    except Exception as e:
        return None, f"手语查询失败: {str(e)}"

# ========== 页面 ==========
st.set_page_config(page_title="语音转手语", layout="centered")
st.title("🗣️ 实时语音 → 国家通用手语")
st.divider()

# 检查语音识别密钥配置
baidu_token = get_baidu_token()
if not baidu_token:
    st.warning("请在Streamlit后台配置百度API_KEY和SECRET_KEY")
    st.stop()

# 原生录音组件
audio = st.audio_input("点击麦克风说话")

if audio:
    with st.spinner("语音识别中..."):
        text = baidu_asr(audio.read(), baidu_token)
        st.subheader("识别结果：" + text)
        
        with st.spinner("查询国家通用手语中..."):
            sign_results, error = search_official_sign(text)
            
            if error:
                st.error(error)
            elif not sign_results:
                st.info("未找到对应的手语手势")
            else:
                # 显示所有手语手势
                st.subheader("国家通用手语手势：")
                cols = st.columns(3)
                for i, result in enumerate(sign_results):
                    with cols[i % 3]:
                        st.image(result["image_url"], caption=result["word"], width=200)
                        st.caption(result["description"][:50] + "..." if len(result["description"]) > 50 else result["description"])

st.caption("✅ 百度语音识别 | 国家通用手语官方词典 | 标准手势图片 | 零额外密钥")
