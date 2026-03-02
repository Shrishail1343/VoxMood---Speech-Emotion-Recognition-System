/**
 * VoxMood — Dashboard Charts
 * Renders: distribution bar, pie, and emotion timeline charts
 */

'use strict';

Chart.defaults.color = 'rgba(240,240,248,0.5)';
Chart.defaults.borderColor = 'rgba(255,255,255,0.06)';
Chart.defaults.font.family = "'DM Sans', sans-serif";

// ── 1. Distribution Bar Chart ───────────────────────────────────
const distBarCtx = document.getElementById('dist-bar-chart')?.getContext('2d');
if (distBarCtx && Object.keys(DISTRIBUTION).length > 0) {
    const labels = Object.keys(DISTRIBUTION);
    const counts = Object.values(DISTRIBUTION);
    const colors = labels.map(l => EMOTION_COLORS[l] || '#8a5cf6');

    new Chart(distBarCtx, {
        type: 'bar',
        data: {
            labels,
            datasets: [{
                label: 'Count',
                data: counts,
                backgroundColor: colors.map(c => c + '44'),
                borderColor: colors,
                borderWidth: 2,
                borderRadius: 8,
                borderSkipped: false,
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            animation: { duration: 900, delay: ctx => ctx.dataIndex * 100 },
            scales: {
                y: {
                    beginAtZero: true,
                    grid: { color: 'rgba(255,255,255,0.05)' },
                    ticks: { stepSize: 1 }
                },
                x: { grid: { display: false } }
            },
            plugins: {
                legend: { display: false },
                tooltip: {
                    callbacks: {
                        label: ctx => ` ${ctx.raw} analyses`
                    }
                }
            }
        }
    });
}

// ── 2. Pie Chart ────────────────────────────────────────────────
const pieCtx = document.getElementById('dist-pie-chart')?.getContext('2d');
if (pieCtx && Object.keys(DISTRIBUTION).length > 0) {
    const labels = Object.keys(DISTRIBUTION);
    const counts = Object.values(DISTRIBUTION);
    const colors = labels.map(l => EMOTION_COLORS[l] || '#8a5cf6');

    new Chart(pieCtx, {
        type: 'doughnut',
        data: {
            labels,
            datasets: [{
                data: counts,
                backgroundColor: colors.map(c => c + '99'),
                borderColor: colors,
                borderWidth: 2,
                hoverOffset: 8
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            animation: { duration: 1000, easing: 'easeInOutQuart' },
            cutout: '62%',
            plugins: {
                legend: {
                    position: 'bottom',
                    labels: {
                        padding: 16,
                        usePointStyle: true,
                        pointStyle: 'circle',
                        font: { size: 12 }
                    }
                },
                tooltip: {
                    callbacks: {
                        label: ctx => ` ${ctx.label}: ${ctx.raw} (${((ctx.raw / counts.reduce((a,b)=>a+b,0))*100).toFixed(1)}%)`
                    }
                }
            }
        }
    });
}

// ── 3. Emotion Timeline (recent analyses) ──────────────────────
const tlCtx = document.getElementById('emotion-timeline-chart')?.getContext('2d');
if (tlCtx && RECENT && RECENT.length > 0) {
    const emotionToNum = { 'Angry': 6, 'Surprise': 5, 'Happy': 4, 'Neutral': 3, 'Fear': 2, 'Sad': 1 };
    const labels  = RECENT.map(r => r.timestamp.slice(5, 16)); // MM-DD HH:MM
    const values  = RECENT.map(r => emotionToNum[r.predicted_emotion] || 3);
    const pColors = RECENT.map(r => EMOTION_COLORS[r.predicted_emotion] || '#8a5cf6');

    new Chart(tlCtx, {
        type: 'line',
        data: {
            labels,
            datasets: [{
                label: 'Emotion',
                data: values,
                borderColor: '#8a5cf6',
                backgroundColor: 'rgba(138,92,246,0.08)',
                fill: true,
                tension: 0.4,
                pointBackgroundColor: pColors,
                pointRadius: 7,
                pointHoverRadius: 10,
                borderWidth: 2
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            animation: { duration: 1200 },
            scales: {
                y: {
                    min: 0,
                    max: 7,
                    grid: { color: 'rgba(255,255,255,0.04)' },
                    ticks: {
                        stepSize: 1,
                        callback: v => ({ 1:'Sad', 2:'Fear', 3:'Neutral', 4:'Happy', 5:'Surprise', 6:'Angry' }[v] || '')
                    }
                },
                x: {
                    grid: { color: 'rgba(255,255,255,0.04)' },
                    ticks: { maxTicksLimit: 10 }
                }
            },
            plugins: {
                legend: { display: false },
                tooltip: {
                    callbacks: {
                        label: ctx => {
                            const item = RECENT[ctx.dataIndex];
                            return ` ${item.predicted_emotion} — ${item.confidence.toFixed(1)}%`;
                        }
                    }
                }
            }
        }
    });
}

// ── Table Search Filter ─────────────────────────────────────────
const searchInput = document.getElementById('table-search');
if (searchInput) {
    searchInput.addEventListener('input', () => {
        const query = searchInput.value.toLowerCase().trim();
        document.querySelectorAll('.table-row').forEach(row => {
            const emotion = (row.dataset.emotion || '').toLowerCase();
            const text = row.textContent.toLowerCase();
            row.classList.toggle('hidden-row', query !== '' && !emotion.includes(query) && !text.includes(query));
        });
    });
}
