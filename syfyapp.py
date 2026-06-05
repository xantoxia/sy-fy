import streamlit as st
import requests
import speech_recognition as sr
from io import BytesIO
from streamlit_mic_recorder import mic_recorder

# 页面配置
st.set_page_config(page_title="语音转手语", layout="centered")
st.title("🗣️语音识别→国标手语生成")
st.divider()

# 手语固定接口
SIGN_API = "https://labs.brand.fun/api/sign?text="

# ==========免密钥ASR函数（Google免费，无KEY）==========
def free_asr(wav_bytes):
    try:
        r = sr.Recognizer()
        audio_file = BytesIO(wav_bytes)
        with sr.AudioFile(audio_file) as source:
            audio = r.record(source)
        res_text = r.recognize_google(audio, language="zh-CN")
        return res_text
    except sr.UnknownValueError:
        return "未能识别语音，请重新录制"
    except sr.RequestError:
        return "ASR接口临时异常"
    except Exception as e:
        return f"识别异常：{str(e)}"
# ==================================================

# 替换成云端可用录音控件
st.subheader("点击下方麦克风按钮录音")
audio_rec = mic_recorder(start_prompt="⏺开始录音", stop_prompt="⏹结束录音", format="wav")

txt_box = st.empty()
img_box = st.empty()

if audio_rec and audio_rec["bytes"]:
    with st.spinner("识别中，正在生成手语..."):
        wav_raw = audio_rec["bytes"]
        text_result = free_asr(wav_raw)
        txt_box.subheader(f"识别文本：{text_result}")
        # 请求手语图片
        try:
            sign_url = SIGN_API + requests.utils.quote(text_result)
            img_box.image(sign_url, width=380)
        except:
            img_box.warning("手语图片加载失败")

st.caption("✅云端网页即用｜无密钥免注册｜浏览器麦克风")
