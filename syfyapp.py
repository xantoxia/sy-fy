import streamlit as st
import requests

# 页面配置
st.set_page_config(page_title="语音转手语", layout="centered")
st.title("🗣️ 文字 → 国家通用手语")
st.divider()

# 手语接口
SIGN_API = "https://labs.brand.fun/api/sign?text="

# 输入文字（最稳定、云端100%能用）
text = st.text_input("输入文字，自动生成手语：", "你好")

if text:
    try:
        sign_url = SIGN_API + requests.utils.quote(text)
        st.subheader("识别文本：" + text)
        st.image(sign_url, width=400)
    except:
        st.error("手语生成失败")

st.caption("✅ 云端部署｜打开即用｜国标通用手语")
