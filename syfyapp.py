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

# ========== 修复版：单组件纯前端录音+官方通信 ==========
recorder_html = """
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

// WebM转WAV（百度ASR只支持WAV）
async function webmToWav(webmBlob) {
    const arrayBuffer = await webmBlob.arrayBuffer();
    const audioContext = new AudioContext({ sampleRate: 16000 });
    const audioBuffer = await audioContext.decodeAudioData(arrayBuffer);
    
    const numChannels = 1;
    const sampleRate = 16000;
    const format = 1; // PCM
    const bitDepth = 16;
    
    const bytesPerSample = bitDepth / 8;
    const blockAlign = numChannels * bytesPerSample;
    const dataLength = audioBuffer.length * blockAlign;
    const buffer = new ArrayBuffer(44 + dataLength);
    const view = new DataView(buffer);
    
    // WAV头
    function writeString(offset, string) {
        for (let i = 0; i < string.length; i++) {
            view.setUint8(offset + i, string.charCodeAt(i));
        }
    }
    
    writeString(0, 'RIFF');
    view.setUint32(4, 36 + dataLength, true);
    writeString(8, 'WAVE');
    writeString(12, 'fmt ');
    view.setUint32(16, 16, true);
    view.setUint16(20, format, true);
    view.setUint16(22, numChannels, true);
    view.setUint32(24, sampleRate, true);
    view.setUint32(28, sampleRate * blockAlign, true);
    view.setUint16(32, blockAlign, true);
    view.setUint16(34, bitDepth, true);
    writeString(36, 'data');
    view.setUint32(40, dataLength, true);
    
    // 音频数据
    const channelData = audioBuffer.getChannelData(0);
    let offset = 44;
    for (let i = 0; i < channelData.length; i++) {
        const sample = Math.max(-1, Math.min(1, channelData[i]));
        view.setInt16(offset, sample < 0 ? sample * 0x8000 : sample * 0x7FFF, true);
        offset += 2;
    }
    
    return new Blob([buffer], { type: 'audio/wav' });
}

recordBtn.addEventListener('click', async () => {
    if (!isRecording) {
        // 开始录音
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        mediaRecorder = new MediaRecorder(stream);
        
        audioChunks = [];
        mediaRecorder.ondataavailable = e => audioChunks.push(e.data);
        
        mediaRecorder.onstop = async () => {
            const webmBlob = new Blob(audioChunks, { type: 'audio/webm' });
            const wavBlob = await webmToWav(webmBlob);
            const reader = new FileReader();
            reader.readAsDataURL(wavBlob);
            reader.onloadend = () => {
                const base64Audio = reader.result.split(',')[1];
                // Streamlit官方通信方式：返回数据给后端
                window.streamlitAPI.setComponentValue(base64Audio);
                status.textContent = "录音完成，正在识别...";
            };
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

# 嵌入录音组件并获取返回值
audio_base64 = st.components.v1.html(recorder_html, height=150)

# 处理识别和手语生成
if audio_base64:
    with st.spinner("正在识别并生成手语..."):
        wav_bytes = base64.b64decode(audio_base64)
        text = baidu_asr(wav_bytes, token)
        st.subheader("识别结果：" + text)
        
        try:
            sign_url = SIGN_URL + requests.utils.quote(text)
            st.image(sign_url, width=400)
        except Exception as e:
            st.error(f"手语生成失败: {str(e)}")

st.caption("✅ 点击开始→点击结束→自动识别→自动出手语 | 云端部署 | 国标手语")
