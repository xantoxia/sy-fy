import streamlit as st
import requests
import base64

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
        res = requests.get(url, timeout=10)
        return res.json().get("access_token")
    except:
        return None

def baidu_asr(wav_bytes, token):
    try:
        speech = base64.b64encode(wav_bytes).decode()
        data = {
            "format": "wav",
            "rate": 16000,
            "dev_pid": 1537,
            "speech": speech,
            "len": len(wav_bytes),
            "access_token": token
        }
        resp = requests.post("https://aip.baidubce.com/rest/2.0/speech/v1/asr", data=data, timeout=15)
        j = resp.json()
        if j.get("err_no") == 0:
            return j["result"][0]
        return f"识别失败: {j.get('err_msg')}"
    except Exception as e:
        return f"识别错误: {str(e)}"

# ========== 页面 ==========
st.set_page_config(page_title="语音转手语", layout="centered")
st.title("🗣️ 实时语音 → 国家通用手语")
st.divider()

token = get_baidu_token()

if not token:
    st.warning("请在 Streamlit 后台配置百度 API_KEY 和 SECRET_KEY")
    st.stop()

# ========== 纯前端HTML5录音组件（彻底绕过Streamlit原生bug）==========
html_recorder = """
<div style="text-align:center;">
    <button id="recordBtn" style="padding:12px 24px; font-size:16px; background:#0078d7; color:white; border:none; border-radius:8px; cursor:pointer;">
        🎙️ 点击开始录音
    </button>
    <p id="status" style="margin-top:10px; color:#666;">准备就绪</p>
</div>

<script>
let mediaRecorder;
let audioChunks = [];
let isRecording = false;
const recordBtn = document.getElementById('recordBtn');
const status = document.getElementById('status');

recordBtn.addEventListener('click', async () => {
    if (!isRecording) {
        // 开始录音
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        mediaRecorder = new MediaRecorder(stream, { mimeType: 'audio/wav' });
        
        audioChunks = [];
        mediaRecorder.ondataavailable = e => audioChunks.push(e.data);
        
        mediaRecorder.onstop = () => {
            const audioBlob = new Blob(audioChunks, { type: 'audio/wav' });
            const reader = new FileReader();
            reader.readAsDataURL(audioBlob);
            reader.onloadend = () => {
                const base64Audio = reader.result.split(',')[1];
                // 传给Streamlit后端
                window.parent.postMessage({ type: 'audio', data: base64Audio }, '*');
            };
            status.textContent = "录音完成，正在识别...";
        };
        
        mediaRecorder.start();
        isRecording = true;
        recordBtn.textContent = "⏹️ 点击结束录音";
        recordBtn.style.background = "#dc3545";
        status.textContent = "正在录音...";
    } else {
        // 结束录音
        mediaRecorder.stop();
        mediaRecorder.stream.getTracks().forEach(track => track.stop());
        isRecording = false;
        recordBtn.textContent = "🎙️ 点击开始录音";
        recordBtn.style.background = "#0078d7";
    }
});
</script>
"""

# 嵌入前端录音组件
st.components.v1.html(html_recorder, height=150)

# 接收前端传过来的音频数据
if "audio_data" not in st.session_state:
    st.session_state.audio_data = None

# 监听前端消息
js_listener = """
<script>
window.addEventListener('message', (event) => {
    if (event.data.type === 'audio') {
        window.parent.document.querySelector('iframe[title="streamlit_component"]').contentWindow.postMessage(
            { type: 'audio', data: event.data.data }, '*'
        );
    }
});
</script>
"""
st.components.v1.html(js_listener, height=0)

# 处理音频识别
if st.session_state.audio_data:
    with st.spinner("正在识别并生成手语..."):
        wav_bytes = base64.b64decode(st.session_state.audio_data)
        text = baidu_asr(wav_bytes, token)
        st.subheader("识别结果：" + text)
        
        try:
            sign_url = SIGN_URL + requests.utils.quote(text)
            st.image(sign_url, width=400)
        except:
            st.error("手语生成失败")
    
    # 清空状态，准备下一次录音
    st.session_state.audio_data = None

st.caption("✅ 纯前端录音｜无Streamlit组件bug｜云端部署｜国标手语")
