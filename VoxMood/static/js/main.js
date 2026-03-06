/**
 * VoxMood — Main JavaScript
 * Handles: file upload UI, drag-drop, MediaRecorder, loading overlay
 * Fixed: live waveform during recording + final waveform after stop
 */

'use strict';

// ── Tab Switcher ───────────────────────────────────────────────
document.querySelectorAll('.tab-btn').forEach(btn => {
    btn.addEventListener('click', () => {
        const tab = btn.dataset.tab;
        document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        document.getElementById('panel-upload')?.classList.add('hidden');
        document.getElementById('panel-record')?.classList.add('hidden');
        const panel = document.getElementById(`panel-${tab}`);
        if (panel) panel.classList.remove('hidden');
    });
});


// ── File Upload UI ─────────────────────────────────────────────
const fileInput     = document.getElementById('file-input');
const dropZone      = document.getElementById('drop-zone');
const filePreview   = document.getElementById('file-preview');
const fileName      = document.getElementById('file-name');
const fileSize      = document.getElementById('file-size');
const fileRemove    = document.getElementById('file-remove');
const analyzeBtn    = document.getElementById('analyze-btn');
const uploadForm    = document.getElementById('upload-form');
const previewCanvas = document.getElementById('preview-canvas');

if (fileInput) {
    fileInput.addEventListener('change', () => {
        if (fileInput.files[0]) showFilePreview(fileInput.files[0]);
    });
}

if (dropZone) {
    dropZone.addEventListener('click', () => fileInput?.click());
    dropZone.addEventListener('dragover', e => { e.preventDefault(); dropZone.classList.add('drag-over'); });
    dropZone.addEventListener('dragleave', () => dropZone.classList.remove('drag-over'));
    dropZone.addEventListener('drop', e => {
        e.preventDefault();
        dropZone.classList.remove('drag-over');
        const file = e.dataTransfer.files[0];
        if (file && fileInput) {
            const dt = new DataTransfer();
            dt.items.add(file);
            fileInput.files = dt.files;
            showFilePreview(file);
        }
    });
}

if (fileRemove) {
    fileRemove.addEventListener('click', () => {
        if (fileInput) fileInput.value = '';
        filePreview?.classList.add('hidden');
        dropZone?.classList.remove('hidden');
        if (analyzeBtn) analyzeBtn.disabled = true;
    });
}

function showFilePreview(file) {
    if (!filePreview) return;
    filePreview.classList.remove('hidden');
    dropZone?.classList.add('hidden');
    if (fileName) fileName.textContent = file.name;
    if (fileSize) fileSize.textContent = formatBytes(file.size);
    if (analyzeBtn) analyzeBtn.disabled = false;

    if (previewCanvas) {
        drawAudioPreview(file, previewCanvas);
    }
}

// ── Draw waveform from any File or Blob ────────────────────────
function drawAudioPreview(fileOrBlob, canvas) {
    const audioCtx = new (window.AudioContext || window.webkitAudioContext)();
    const reader   = new FileReader();

    reader.onload = async e => {
        try {
            const buffer   = await audioCtx.decodeAudioData(e.target.result);
            const rawData  = buffer.getChannelData(0);
            const samples  = canvas.offsetWidth || 300;
            const blockSize = Math.floor(rawData.length / samples);
            const filtered = [];
            for (let i = 0; i < samples; i++) {
                let sum = 0;
                for (let j = 0; j < blockSize; j++) {
                    sum += Math.abs(rawData[i * blockSize + j]);
                }
                filtered.push(sum / blockSize);
            }
            drawWaveformOnCanvas(canvas, filtered, '#8a5cf6', 'transparent');
        } catch (err) {
            console.warn('Waveform decode error:', err);
            drawPlaceholderWaveform(canvas, '#8a5cf6');
        }
    };

    reader.onerror = () => drawPlaceholderWaveform(canvas, '#8a5cf6');
    reader.readAsArrayBuffer(fileOrBlob);
}

function drawPlaceholderWaveform(canvas, color) {
    const ctx = canvas.getContext('2d');
    const W   = canvas.offsetWidth  || 300;
    const H   = canvas.offsetHeight || 60;
    canvas.width  = W;
    canvas.height = H;
    ctx.clearRect(0, 0, W, H);
    const bars = 60;
    const bw   = W / bars;
    for (let i = 0; i < bars; i++) {
        const h = (0.2 + Math.random() * 0.6) * H;
        ctx.fillStyle = color + '88';
        ctx.fillRect(i * bw + 1, (H - h) / 2, bw - 2, h);
    }
}


// ── Loading Overlay ────────────────────────────────────────────
if (uploadForm) {
    uploadForm.addEventListener('submit', e => {
        if (!fileInput?.files?.[0]) { e.preventDefault(); return; }
        showLoading();
    });
}
document.getElementById('record-form')?.addEventListener('submit', () => showLoading());

function showLoading() {
    const overlay = document.getElementById('loading-overlay');
    if (!overlay) return;
    overlay.classList.remove('hidden');
    const steps  = ['step-1', 'step-2', 'step-3', 'step-4'];
    const delays = [0, 1200, 2400, 3600];
    steps.forEach((id, i) => {
        setTimeout(() => {
            const el = document.getElementById(id);
            if (!el) return;
            steps.slice(0, i).forEach(prev => {
                document.getElementById(prev)?.classList.remove('active');
                document.getElementById(prev)?.classList.add('done');
            });
            el.classList.add('active');
        }, delays[i]);
    });
}


// ── MediaRecorder (Live Recording) ────────────────────────────
const btnRecord         = document.getElementById('btn-record');
const btnStop           = document.getElementById('btn-stop');
const timerEl           = document.getElementById('recorder-timer');
const statusEl          = document.getElementById('recorder-status');
const vizRing           = document.getElementById('viz-ring');
const recordedPreview   = document.getElementById('recorded-preview');
const recordedAudio     = document.getElementById('recorded-audio');
const recordedFileInput = document.getElementById('recorded-file-input');

let liveCanvasEl  = null;
let liveCtx       = null;
let analyserNode  = null;
let vizAnimFrame  = null;
let mediaRecorder = null;
let audioChunks   = [];
let timerInterval = null;
let seconds       = 0;

if (btnRecord) btnRecord.addEventListener('click', startRecording);
if (btnStop)   btnStop.addEventListener('click', stopRecording);

async function startRecording() {
    try {
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        audioChunks  = [];

        // Live waveform analyser
        const audioCtx = new (window.AudioContext || window.webkitAudioContext)();
        const source   = audioCtx.createMediaStreamSource(stream);
        analyserNode   = audioCtx.createAnalyser();
        analyserNode.fftSize = 256;
        source.connect(analyserNode);

        // Create canvas dynamically if not already present
        if (!liveCanvasEl) {
            liveCanvasEl = document.createElement('canvas');
            liveCanvasEl.id = 'live-waveform-canvas';
            liveCanvasEl.style.cssText = `
                width: 100%; height: 60px; display: block;
                border-radius: 8px; margin: 12px 0;
                background: rgba(255,255,255,0.04);
            `;
            const controls = document.querySelector('.recorder-controls');
            if (controls) {
                controls.after(liveCanvasEl);
            } else {
                btnStop?.parentNode?.appendChild(liveCanvasEl);
            }
        }
        liveCanvasEl.style.display = 'block';
        liveCtx = liveCanvasEl.getContext('2d');
        drawLiveWaveform();

        // MediaRecorder
        mediaRecorder = new MediaRecorder(stream, { mimeType: getSupportedMimeType() });
        mediaRecorder.ondataavailable = e => { if (e.data.size > 0) audioChunks.push(e.data); };
        mediaRecorder.onstop = handleRecordingStop;
        mediaRecorder.start(100);

        // UI
        btnRecord?.classList.add('hidden');
        btnStop?.classList.remove('hidden');
        vizRing?.classList.add('recording');
        if (statusEl) statusEl.textContent = 'Recording in progress...';
        recordedPreview?.classList.add('hidden');

        // Timer
        seconds = 0;
        updateTimer();
        timerInterval = setInterval(() => { seconds++; updateTimer(); }, 1000);

    } catch (err) {
        if (statusEl) statusEl.textContent = 'Microphone access denied.';
        console.error('Microphone error:', err);
    }
}

function stopRecording() {
    if (mediaRecorder && mediaRecorder.state !== 'inactive') {
        mediaRecorder.stop();
        mediaRecorder.stream.getTracks().forEach(t => t.stop());
    }
    clearInterval(timerInterval);
    if (vizAnimFrame) { cancelAnimationFrame(vizAnimFrame); vizAnimFrame = null; }
    btnRecord?.classList.remove('hidden');
    btnStop?.classList.add('hidden');
    vizRing?.classList.remove('recording');
    if (statusEl) statusEl.textContent = 'Processing recording...';
}

function handleRecordingStop() {
    const mimeType = getSupportedMimeType();
    const blob     = new Blob(audioChunks, { type: mimeType });
    const url      = URL.createObjectURL(blob);

    if (recordedAudio) recordedAudio.src = url;
    if (statusEl) statusEl.textContent = 'Recording ready — click Analyze to process';
    recordedPreview?.classList.remove('hidden');

    // Attach to hidden file input
    const ext  = mimeType.includes('ogg') ? 'ogg' : mimeType.includes('webm') ? 'webm' : 'wav';
    const file = new File([blob], `recording.${ext}`, { type: mimeType });
    if (recordedFileInput) {
        const dt = new DataTransfer();
        dt.items.add(file);
        recordedFileInput.files = dt.files;
    }

    // Draw final waveform from the recorded blob
    if (liveCanvasEl) {
        drawAudioPreview(blob, liveCanvasEl);
    }
}

// ── Real-time waveform animation during recording ──────────────
function drawLiveWaveform() {
    if (!analyserNode || !liveCtx || !liveCanvasEl) return;

    const bufferLength = analyserNode.frequencyBinCount;
    const dataArray    = new Uint8Array(bufferLength);

    function draw() {
        vizAnimFrame = requestAnimationFrame(draw);
        analyserNode.getByteTimeDomainData(dataArray);

        const W = liveCanvasEl.offsetWidth  || 300;
        const H = liveCanvasEl.offsetHeight || 60;
        liveCanvasEl.width  = W;
        liveCanvasEl.height = H;

        liveCtx.clearRect(0, 0, W, H);
        liveCtx.lineWidth   = 2;
        liveCtx.strokeStyle = '#8a5cf6';
        liveCtx.beginPath();

        const sliceWidth = W / bufferLength;
        let x = 0;
        for (let i = 0; i < bufferLength; i++) {
            const v = dataArray[i] / 128.0;
            const y = (v * H) / 2;
            i === 0 ? liveCtx.moveTo(x, y) : liveCtx.lineTo(x, y);
            x += sliceWidth;
        }
        liveCtx.lineTo(W, H / 2);
        liveCtx.stroke();

        // Gradient fill
        liveCtx.lineTo(W, H);
        liveCtx.lineTo(0, H);
        liveCtx.closePath();
        const grad = liveCtx.createLinearGradient(0, 0, 0, H);
        grad.addColorStop(0, 'rgba(138, 92, 246, 0.3)');
        grad.addColorStop(1, 'rgba(138, 92, 246, 0)');
        liveCtx.fillStyle = grad;
        liveCtx.fill();
    }

    draw();
}

function updateTimer() {
    const m = Math.floor(seconds / 60);
    const s = seconds % 60;
    if (timerEl) timerEl.textContent = `${m}:${s.toString().padStart(2, '0')}`;
}

function getSupportedMimeType() {
    const types = ['audio/webm;codecs=opus', 'audio/webm', 'audio/ogg;codecs=opus', 'audio/wav'];
    return types.find(t => MediaRecorder.isTypeSupported(t)) || 'audio/webm';
}


// ── Waveform Canvas Utility ────────────────────────────────────
function drawWaveformOnCanvas(canvas, data, color = '#8a5cf6', bgColor = 'transparent') {
    const ctx = canvas.getContext('2d');
    const W   = canvas.offsetWidth  || canvas.width  || 300;
    const H   = canvas.offsetHeight || canvas.height || 60;
    canvas.width  = W;
    canvas.height = H;

    ctx.clearRect(0, 0, W, H);
    if (bgColor !== 'transparent') {
        ctx.fillStyle = bgColor;
        ctx.fillRect(0, 0, W, H);
    }

    if (!data || data.length === 0) {
        ctx.beginPath();
        ctx.moveTo(0, H / 2);
        ctx.lineTo(W, H / 2);
        ctx.strokeStyle = color;
        ctx.lineWidth = 1.5;
        ctx.stroke();
        return;
    }

    const amp = H / 2;
    ctx.beginPath();
    for (let i = 0; i < data.length; i++) {
        const x = (i / data.length) * W;
        const y = amp - data[i] * amp * 0.9;
        i === 0 ? ctx.moveTo(x, y) : ctx.lineTo(x, y);
    }
    ctx.strokeStyle = color;
    ctx.lineWidth   = 1.5;
    ctx.stroke();

    ctx.lineTo(W, amp);
    ctx.lineTo(0, amp);
    ctx.closePath();
    const grad = ctx.createLinearGradient(0, 0, 0, H);
    grad.addColorStop(0, color + '44');
    grad.addColorStop(1, 'transparent');
    ctx.fillStyle = grad;
    ctx.fill();
}


// ── Helpers ───────────────────────────────────────────────────
function formatBytes(bytes) {
    if (bytes < 1024)        return bytes + ' B';
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
    return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
}

setTimeout(() => {
    document.querySelectorAll('.flash').forEach(el => {
        el.style.transition = 'opacity 0.5s';
        el.style.opacity    = '0';
        setTimeout(() => el.remove(), 500);
    });
}, 5000);

window.VoxMood = { drawWaveformOnCanvas };