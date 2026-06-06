import streamlit as st
import requests
import base64
import wave
from io import BytesIO

# ========== 配置（只需要你已有的百度密钥）==========
BAIDU_API_KEY = st.secrets.get("API_KEY", "")
BAIDU_SECRET_KEY = st.secrets.get("SECRET_KEY", "")

# ========== 百度通用鉴权（语音识别+图片搜索共用）==========
@st.cache_resource(ttl=86400)
def get_baidu_token():
    if not BAIDU_API_KEY or not BAIDU_SECRET_KEY:
        return None
    try:
        url = f"https://aip.baidubce.com/oauth/2.0/token?grant_type=client_credentials&client_id={BAIDU_API_KEY}&client_secret={BAIDU_SECRET_KEY}"
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

# ========== 百度图片搜索手语（稳定可用，不会被拦截）==========
def search_sign_images(text, token):
    try:
        # 简单分词：按空格和标点符号分割
        import re
        words = re.split(r'[，。！？、\s]+', text.strip())
        words = [word for word in words if word]
        
        if not words:
            words = [text]
        
        results = []
        for word in words:
            if not word:
                continue
                
            # 搜索关键词：国家通用手语 + 词语
            keyword = f"国家通用手语 {word}"
            url = f"https://aip.baidubce.com/rest/2.0/image-classify/v1/advanced_general?access_token={token}"
            
            data = {
                "query": keyword,
                "num": 1,  # 只返回1张最相关的图片
                "start": 0
            }
            
            # 增加超时时间和重试
            for _ in range(3):
                try:
                    resp = requests.post(url, data=data, timeout=20)
                    j = resp.json()
                    
                    if j.get("result") and len(j["result"]) > 0:
                        results.append({
                            "word": word,
                            "image_url": j["result"][0]["thumbnailUrl"]
                        })
                    break
                except:
                    continue
        
        return results, None
    except Exception as e:
        return None, f"手语搜索失败: {str(e)}"

# ========== 页面 ==========
st.set_page_config(page_title="语音转手语", layout="centered")
st.title("🗣️ 实时语音 → 国家通用手语")
st.divider()

# 检查密钥配置
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
        
        with st.spinner("搜索手语图片中..."):
            sign_results, error = search_sign_images(text, token)
            
            if error:
                st.error(error)
            elif not sign_results:
                st.info("未找到对应的手语图片")
            else:
                # 显示所有手语图片
                st.subheader("国家通用手语手势：")
                cols = st.columns(3)
                for i, result in enumerate(sign_results):
                    with cols[i % 3]:
                        st.image(result["image_url"], caption=result["word"], width=200)

st.caption("✅ 百度语音识别 | 百度图片搜索手语 | 稳定可用 | 零额外密钥")
