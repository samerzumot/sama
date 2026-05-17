/* ─────────────────────────────────────────
   EQ INSIGHTS — JS
   Coherence ring, radar chart, bar animations
   ───────────────────────────────────────── */

document.addEventListener('DOMContentLoaded', () => {

    /* ── Scroll animations (fade-in) ─────── */
    const fadeObs = new IntersectionObserver((entries) => {
        entries.forEach(e => {
            if (e.isIntersecting) e.target.classList.add('visible');
        });
    }, { threshold: 0.1 });

    document.querySelectorAll('.eq-section .fade-in').forEach(el => fadeObs.observe(el));


    /* ── Coherence ring ──────────────────── */
    const ringEl = document.querySelector('.ring-progress');
    const numEl = document.querySelector('.coherence-number');

    if (ringEl && numEl) {
        const ringObs = new IntersectionObserver((entries) => {
            entries.forEach(e => {
                if (e.isIntersecting) {
                    const target = parseFloat(ringEl.dataset.target);
                    const circ = 2 * Math.PI * 85;
                    setTimeout(() => {
                        ringEl.style.strokeDashoffset = circ * (1 - target);
                    }, 400);
                    countUp(numEl, 0, target, 1800);
                    ringObs.unobserve(e.target);
                }
            });
        }, { threshold: 0.3 });
        ringObs.observe(document.getElementById('coherence'));
    }

    function countUp(el, from, to, dur) {
        const t0 = performance.now();
        (function tick(now) {
            const p = Math.min((now - t0) / dur, 1);
            const ease = 1 - Math.pow(1 - p, 3);
            el.textContent = (from + (to - from) * ease).toFixed(1);
            if (p < 1) requestAnimationFrame(tick);
        })(t0);
    }


    /* ── Dimension bars ──────────────────── */
    const dimList = document.querySelector('.dim-list');
    if (dimList) {
        const dimObs = new IntersectionObserver((entries) => {
            entries.forEach(e => {
                if (e.isIntersecting) {
                    dimList.querySelectorAll('.dim-fill').forEach((bar, i) => {
                        setTimeout(() => bar.classList.add('animated'), i * 120);
                    });
                    dimObs.unobserve(e.target);
                }
            });
        }, { threshold: 0.2 });
        dimObs.observe(dimList);
    }


    /* ── Radar chart ─────────────────────── */
    const canvas = document.getElementById('radar-chart');
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    const dpr = window.devicePixelRatio || 1;
    canvas.width = 400 * dpr;
    canvas.height = 400 * dpr;
    canvas.style.width = '100%';
    canvas.style.height = '100%';
    ctx.scale(dpr, dpr);

    const dims = [
        { label: 'Self\nAwareness', value: 0.80 },
        { label: 'Emotional\nRegulation', value: 1.00 },
        { label: 'Motivation', value: 0.00 },
        { label: 'Self\nDisclosure', value: 0.66 },
        { label: 'Valence\nAwareness', value: 0.67 }
    ];

    const cx = 200, cy = 200, maxR = 130, n = dims.length;
    const step = (2 * Math.PI) / n;
    const start = -Math.PI / 2;

    // Use site colors
    const fillColor = 'rgba(66, 133, 244, 0.15)';   // --accent-blue at low alpha
    const strokeColor = 'rgba(66, 133, 244, 0.5)';
    const dotColor = '#4285F4';
    const gridColor = 'rgba(255, 255, 255, 0.05)';
    const labelColor = 'rgba(255, 255, 255, 0.4)';

    function draw(p) {
        ctx.clearRect(0, 0, 400, 400);

        // Grid
        for (let r = 0.25; r <= 1; r += 0.25) {
            ctx.beginPath();
            for (let i = 0; i <= n; i++) {
                const a = start + i * step;
                const x = cx + Math.cos(a) * maxR * r;
                const y = cy + Math.sin(a) * maxR * r;
                i === 0 ? ctx.moveTo(x, y) : ctx.lineTo(x, y);
            }
            ctx.closePath();
            ctx.strokeStyle = gridColor;
            ctx.lineWidth = 1;
            ctx.stroke();
        }

        // Axes
        for (let i = 0; i < n; i++) {
            const a = start + i * step;
            ctx.beginPath();
            ctx.moveTo(cx, cy);
            ctx.lineTo(cx + Math.cos(a) * maxR, cy + Math.sin(a) * maxR);
            ctx.strokeStyle = gridColor;
            ctx.stroke();
        }

        // Data polygon
        ctx.beginPath();
        for (let i = 0; i <= n; i++) {
            const idx = i % n;
            const a = start + idx * step;
            const v = Math.max(dims[idx].value * p, 0.02);
            const x = cx + Math.cos(a) * maxR * v;
            const y = cy + Math.sin(a) * maxR * v;
            i === 0 ? ctx.moveTo(x, y) : ctx.lineTo(x, y);
        }
        ctx.closePath();
        ctx.fillStyle = fillColor;
        ctx.fill();
        ctx.strokeStyle = strokeColor;
        ctx.lineWidth = 2;
        ctx.stroke();

        // Dots
        for (let i = 0; i < n; i++) {
            const a = start + i * step;
            const v = Math.max(dims[i].value * p, 0.02);
            const x = cx + Math.cos(a) * maxR * v;
            const y = cy + Math.sin(a) * maxR * v;
            ctx.beginPath();
            ctx.arc(x, y, 4, 0, Math.PI * 2);
            ctx.fillStyle = dotColor;
            ctx.fill();
        }

        // Labels
        ctx.textAlign = 'center';
        ctx.textBaseline = 'middle';
        ctx.fillStyle = labelColor;
        ctx.font = '11px Inter, system-ui, sans-serif';
        for (let i = 0; i < n; i++) {
            const a = start + i * step;
            const lx = cx + Math.cos(a) * (maxR + 28);
            const ly = cy + Math.sin(a) * (maxR + 28);
            dims[i].label.split('\n').forEach((line, li, arr) => {
                ctx.fillText(line, lx, ly + (li - (arr.length - 1) / 2) * 14);
            });
        }
    }

    draw(0);

    const radarObs = new IntersectionObserver((entries) => {
        entries.forEach(e => {
            if (e.isIntersecting) {
                const t0 = performance.now();
                (function anim(now) {
                    const p = Math.min((now - t0) / 1400, 1);
                    draw(1 - Math.pow(1 - p, 3));
                    if (p < 1) requestAnimationFrame(anim);
                })(t0);
                radarObs.unobserve(e.target);
            }
        });
    }, { threshold: 0.3 });

    radarObs.observe(canvas.closest('.radar-card') || canvas);
});
