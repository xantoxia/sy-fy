import streamlit as st
import requests

# 页面基础配置
st.set_page_config(page_title="实时语音转手语", layout="centered")
st.title("🗣️ 实时语音 → 国家通用手语")
st.divider()

# ----------------【配置项，填入自己百度密钥】----------------
# 去百度智能云-语音识别创建应用获取
BAIDU_API_KEY = "填入你的API_KEY"
BAIDU_SECRET = "填入你的SECRET_KEY"
SIGN_API = "https://labs.brand.fun/api/sign?text="
# ----------------------------------------------------------

# 缓存获取百度鉴权Token（24小时有效）
@st.cache_resource(ttl=86400)
def get_token():
    url = f"https://aip.baidubce.com/oauth/2.0/token?grant_type=client_credentials&client_id={BAIDU_API_KEY}&client_secret={BAIDU_SECRET}"
    res = requests.get(url)
    return res.json()["access_token"]

token = get_token()
audio_file = st.audio_input("点击麦克风，按住说话完成识别", format="wav")
text_box = st.empty()
sign_box = st.empty()

# 百度一句话语音识别
def baidu_asr(wav_bytes):
    headers = {"Content-Type":"application/x-www-form-urlencoded"}
    data = {
        "access_token":token,
        "format":"wav",
        "rate":16000,
        "dev_pid":1537, # 1537=普通话
        "speech":requests.utils.b64encode(wav_bytes).decode()
    }
    resp = requests.post("https://aip.baidubce.com/rest/2.0/speech/v1/asr",data=data,headers=headers,timeout=12)
    ret = resp.json()
    if ret["err_no"] == 0:
        return ret["result"][0]
    else:
        return f"识别异常：{ret['err_msg']}"

# 业务逻辑
if audio_file:
    with st.spinner("语音识别中..."):
        wav_data = audio_file.read()
        res_text = baidu_asr(wav_data)
        text_box.subheader(f"识别结果：{res_text}")
        # 请求手语图片
        try:
            sign_img_url = SIGN_API + requests.utils.quote(res_text)
            sign_box.image(sign_img_url,width=360)
        except:
            sign_box.warning("手语资源加载失败")

st.caption("✅云端部署 | 全浏览器免安装使用 | 国标通用手语")
