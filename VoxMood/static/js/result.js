/**
 * VoxMood — Result Page Charts
 * Renders: waveform, emotion bar chart, radar chart, timeline
 * Fixed: waveform loads from audio file directly if DB data is empty (webm recordings)
 */

'use strict';

// ── Chart defaults ─────────────────────────────────────────────
Chart.defaults.color = 'rgba(240,240,248,0.5)';
Chart.defaults.borderColor = 'rgba(255,255,255,0.06)';
Chart.defaults.font.family = "'DM Sans', sans-serif";

const EMOTIONS     = Object.keys(ALL_SCORES);
const SCORES       = Object.values(ALL_SCORES);
const COLORS_ARRAY = EMOTIONS.map(e => EMOTION_COLORS[e] || '#8a5cf6');
const PRIMARY_COLOR = EMOTION_COLORS[PRIMARY_EMOTION] || '#8a5cf6';

// ── 1. Waveform ────────────────────────────────────────────────
// Get filename directly from the page (meta-value first element)
const filenameEl = document.querySelector('.meta-value');
const FILENAME   = filenameEl ? filenameEl.textContent.trim() : null;

if (WAVEFORM_DATA && WAVEFORM_DATA.length > 0) {
    // DB has waveform data — use it directly
    renderWaveformChart(WAVEFORM_DATA);
} else if (FILENAME) {
    // DB empty (webm recording) — fetch audio file and decode in browser
    fetchAndDrawWaveform(FILENAME);
} else {
    drawFallbackWaveform();
}

function fetchAndDrawWaveform(filename) {
    const audioUrl = `/static/uploads/${filename}`;
    fetch(audioUrl)
        .then(res => {
            if (!res.ok) throw new Error(`Cannot fetch: ${audioUrl}`);
            return res.arrayBuffer();
        })
        .then(buffer => {
            const audioCtx = new (window.AudioContext || window.webkitAudioContext)();
            return audioCtx.decodeAudioData(buffer);
        })
        .then(audioBuffer => {
            const rawData   = audioBuffer.getChannelData(0);
            const samples   = 300;
            const blockSize = Math.floor(rawData.length / samples);
            const filtered  = [];
            for (let i = 0; i < samples; i++) {
                let sum = 0;
                for (let j = 0; j < blockSize; j++) {
                    sum += Math.abs(rawData[i * blockSize + j] || 0);
                }
                filtered.push((sum / blockSize) * 100);
            }
            renderWaveformChart(filtered);
        })
        .catch(err => {
            console.warn('Waveform fetch/decode failed:', err);
            drawFallbackWaveform();
        });
}

function renderWaveformChart(data) {
    const wCtx = document.getElementById('waveform-chart')?.getContext('2d');
    if (!wCtx) return;

    new Chart(wCtx, {
        type: 'line',
        data: {
            labels: data.map((_, i) => i),
            datasets: [{
                data,
                borderColor: PRIMARY_COLOR,
                borderWidth: 1.5,
                fill: true,
                backgroundColor: createGradient(wCtx, PRIMARY_COLOR),
                pointRadius: 0,
                tension: 0.3
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            animation: { duration: 1000, easing: 'easeInOutCubic' },
            scales: {
                x: { display: false },
                y: {
                    display: true,
                    grid: { color: 'rgba(255,255,255,0.04)' },
                    ticks: { maxTicksLimit: 5 }
                }
            },
            plugins: { legend: { display: false }, tooltip: { enabled: false } }
        }
    });
}

function drawFallbackWaveform() {
    // Draw random bars as a visual placeholder
    const canvas = document.getElementById('waveform-chart');
    if (!canvas) return;
    // Small delay so canvas is sized by browser
    setTimeout(() => {
        const ctx = canvas.getContext('2d');
        const W   = canvas.offsetWidth  || 800;
        const H   = canvas.offsetHeight || 200;
        canvas.width  = W;
        canvas.height = H;
        ctx.clearRect(0, 0, W, H);
        const bars = 100;
        const bw   = W / bars;
        for (let i = 0; i < bars; i++) {
            const h = (0.1 + Math.random() * 0.6) * H;
            ctx.fillStyle = PRIMARY_COLOR + '55';
            ctx.fillRect(i * bw + 1, (H - h) / 2, bw - 2, h);
        }
    }, 100);
}


// ── 2. Emotion Confidence Bar Chart ───────────────────────────
const barCtx = document.getElementById('emotion-bar-chart')?.getContext('2d');
if (barCtx && EMOTIONS.length > 0) {
    const sorted = EMOTIONS
        .map((e, i) => ({ e, s: SCORES[i], c: COLORS_ARRAY[i] }))
        .sort((a, b) => b.s - a.s);

    new Chart(barCtx, {
        type: 'bar',
        data: {
            labels: sorted.map(x => x.e),
            datasets: [{
                data: sorted.map(x => x.s),
                backgroundColor: sorted.map(x => x.c + '33'),
                borderColor: sorted.map(x => x.c),
                borderWidth: 2,
                borderRadius: 8,
                borderSkipped: false,
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            animation: { duration: 900, delay: ctx => ctx.dataIndex * 80 },
            indexAxis: 'y',
            scales: {
                x: {
                    max: 100,
                    grid: { color: 'rgba(255,255,255,0.05)' },
                    ticks: { callback: v => v + '%' }
                },
                y: { grid: { display: false } }
            },
            plugins: {
                legend: { display: false },
                tooltip: { callbacks: { label: ctx => ` ${ctx.raw.toFixed(1)}%` } }
            }
        }
    });
}


// ── 3. Radar Chart ─────────────────────────────────────────────
const radarCtx = document.getElementById('emotion-radar-chart')?.getContext('2d');
if (radarCtx && EMOTIONS.length > 0) {
    new Chart(radarCtx, {
        type: 'radar',
        data: {
            labels: EMOTIONS,
            datasets: [{
                label: 'Emotion Profile',
                data: SCORES,
                borderColor: PRIMARY_COLOR,
                backgroundColor: PRIMARY_COLOR + '22',
                borderWidth: 2,
                pointBackgroundColor: COLORS_ARRAY,
                pointRadius: 5,
                pointHoverRadius: 7
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            animation: { duration: 1000, easing: 'easeInOutQuart' },
            scales: {
                r: {
                    max: 100, min: 0,
                    grid: { color: 'rgba(255,255,255,0.06)' },
                    angleLines: { color: 'rgba(255,255,255,0.06)' },
                    ticks: {
                        stepSize: 25,
                        backdropColor: 'transparent',
                        color: 'rgba(255,255,255,0.35)',
                        font: { size: 10 }
                    },
                    pointLabels: { color: 'rgba(240,240,248,0.7)', font: { size: 12 } }
                }
            },
            plugins: { legend: { display: false } }
        }
    });
}


// ── 4. Emotion Timeline Chart ──────────────────────────────────
if (TIMELINE_DATA && TIMELINE_DATA.length > 1) {
    const timelineSection = document.getElementById('timeline-section');
    if (timelineSection) timelineSection.style.display = '';

    const tlCtx = document.getElementById('timeline-chart')?.getContext('2d');
    if (tlCtx) {
        // Include all 7 emotion variants
        const emotionToNum = {
            'Angry': 7, 'Disgust': 6,
            'Surprise': 5, 'Surprised': 5,
            'Happy': 4, 'Neutral': 3,
            'Fear': 2, 'Fearful': 2,
            'Sad': 1
        };

        new Chart(tlCtx, {
            type: 'line',
            data: {
                labels: TIMELINE_DATA.map(d => `${d.time}s`),
                datasets: [{
                    label: 'Emotion',
                    data: TIMELINE_DATA.map(d => emotionToNum[d.emotion] || 3),
                    borderColor: '#8a5cf6',
                    backgroundColor: 'rgba(138,92,246,0.1)',
                    fill: true,
                    tension: 0.4,
                    pointBackgroundColor: TIMELINE_DATA.map(d => d.color || '#8a5cf6'),
                    pointRadius: 6,
                    pointHoverRadius: 9,
                    borderWidth: 2
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                animation: { duration: 1200 },
                scales: {
                    y: {
                        min: 0, max: 8,
                        grid: { color: 'rgba(255,255,255,0.05)' },
                        ticks: {
                            stepSize: 1,
                            callback: v => {
                                const map = {
                                    1: 'Sad', 2: 'Fearful', 3: 'Neutral',
                                    4: 'Happy', 5: 'Surprised', 6: 'Disgust', 7: 'Angry'
                                };
                                return map[v] || '';
                            }
                        }
                    },
                    x: { grid: { color: 'rgba(255,255,255,0.05)' } }
                },
                plugins: {
                    legend: { display: false },
                    tooltip: {
                        callbacks: {
                            label: ctx => {
                                const d = TIMELINE_DATA[ctx.dataIndex];
                                return ` ${d.emotion} (${d.confidence.toFixed(1)}%)`;
                            }
                        }
                    }
                }
            }
        });
    }
}


// ── Gradient helper ────────────────────────────────────────────
function createGradient(ctx, color) {
    const gradient = ctx.createLinearGradient(0, 0, 0, 240);
    gradient.addColorStop(0, hexToRgba(color, 0.3));
    gradient.addColorStop(1, hexToRgba(color, 0.0));
    return gradient;
}

function hexToRgba(hex, alpha) {
    const r = parseInt(hex.slice(1, 3), 16);
    const g = parseInt(hex.slice(3, 5), 16);
    const b = parseInt(hex.slice(5, 7), 16);
    return `rgba(${r},${g},${b},${alpha})`;
}


// ── Animate score bars on load ─────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
    document.querySelectorAll('.score-bar-fill').forEach(bar => {
        const target = bar.style.width;
        bar.style.width = '0%';
        setTimeout(() => { bar.style.width = target; }, 200);
    });
});