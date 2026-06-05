import streamlit as st
import requests
import speech_recognition as sr
from io import BytesIO

# 页面配置
st.set_page_config(page_title="语音转手语", layout="centered")
st.title("🗣️语音识别→国标手语生成")
st.divider()

# 手语固定接口
SIGN_API = "https://labs.brand.fun/api/sign?text="

# ==========【免密钥ASR函数：Google免费公共接口，无任何key】==========
def free_asr(wav_bytes):
    try:
        r = sr.Recognizer()
        audio_file = BytesIO(wav_bytes)
        with sr.AudioFile(audio_file) as source:
            audio = r.record(source)
        # 中文识别 zh-CN，完全免费免注册
        res_text = r.recognize_google(audio, language="zh-CN")
        return res_text
    except sr.UnknownValueError:
        return "未能识别语音内容，请重新录制"
    except sr.RequestError:
        return "云端ASR接口暂时访问异常"
    except Exception as e:
        return f"识别出错：{str(e)}"
# ==================================================================

# 录音组件
audio = st.audio_input("点击麦克风录制语音（wav）", format="wav")
txt_box = st.empty()
img_box = st.empty()

if audio:
    with st.spinner("语音识别+手语生成中..."):
        wav_raw = audio.read()
        text_result = free_asr(wav_raw)
        txt_box.subheader(f"识别文本：{text_result}")
        # 生成手语图片
        try:
            sign_url = SIGN_API + requests.utils.quote(text_result)
            img_box.image(sign_url, width=380)
        except:
            img_box.warning("手语图片加载失败")

st.caption("✅云端部署 | 全平台网页打开即用 | 无密钥无需注册")
