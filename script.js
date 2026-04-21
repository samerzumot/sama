document.addEventListener('DOMContentLoaded', () => {
    /* ----------------------------------------------------
       THEME SWITCHER
    ---------------------------------------------------- */
    const body = document.body;
    const heroSection = document.querySelector('.hero');
    const header = document.querySelector('.sticky-header');

    window.addEventListener('scroll', () => {
        const scrollPos = window.scrollY;
        const triggerPoint = window.innerHeight * 0.6; // Switch after 60% of hero

        if (scrollPos > triggerPoint) {
            body.classList.remove('light-theme');
            body.classList.add('dark-theme');
            // header button adjustments handled by CSS
        } else {
            body.classList.add('light-theme');
            body.classList.remove('dark-theme');
        }
    });


    /* ----------------------------------------------------
       SCROLL ANIMATIONS (Intersection Observer)
    ---------------------------------------------------- */
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('visible');
            }
        });
    }, { threshold: 0.1 });

    document.querySelectorAll('.fade-in').forEach(el => observer.observe(el));


    /* ----------------------------------------------------
       ROTATING WORD ANIMATION
    ---------------------------------------------------- */
    const rotatingWord = document.getElementById('rotating-word');
    const words = ['counselling', 'tutoring', 'consulting'];
    let wordIndex = 0;

    if (rotatingWord) {
        setInterval(() => {
            // Fade out
            rotatingWord.style.opacity = '0';
            rotatingWord.style.transform = 'translateY(6px)';

            setTimeout(() => {
                // Swap word
                wordIndex = (wordIndex + 1) % words.length;
                rotatingWord.textContent = words[wordIndex];

                // Fade in
                rotatingWord.style.opacity = '1';
                rotatingWord.style.transform = 'translateY(0)';
            }, 350);
        }, 2200);
    }


    /* ----------------------------------------------------
       PARTICLE CANVAS ENGINE
    ---------------------------------------------------- */
    const canvas = document.getElementById('bg-canvas');
    const ctx = canvas.getContext('2d');
    let width, height;
    let particles = [];

    // Mouse State
    let mouse = { x: -1000, y: -1000 };

    window.addEventListener('mousemove', (e) => {
        mouse.x = e.clientX;
        mouse.y = e.clientY;
    });

    function resize() {
        width = window.innerWidth;
        height = window.innerHeight;
        canvas.width = width;
        canvas.height = height;
        initParticles();
    }

    window.addEventListener('resize', resize);

    class Particle {
        constructor() {
            this.x = Math.random() * width;
            this.y = Math.random() * height;
            this.vx = (Math.random() - 0.5) * 0.5; // low velocity
            this.vy = (Math.random() - 0.5) * 0.5;
            this.size = Math.random() * 2 + 1;
            // Colors will be determined effectively by theme state or blending
            // We use a base color that works on both or shifts
            this.baseAlpha = Math.random() * 0.5 + 0.1;
        }

        update() {
            // Movement
            this.x += this.vx;
            this.y += this.vy;

            // Bounce off edges
            if (this.x < 0 || this.x > width) this.vx *= -1;
            if (this.y < 0 || this.y > height) this.vy *= -1;

            // Mouse Interaction (Push Effect)
            const dx = mouse.x - this.x;
            const dy = mouse.y - this.y;
            const dist = Math.sqrt(dx * dx + dy * dy);
            const forceDist = 150;

            if (dist < forceDist) {
                const angle = Math.atan2(dy, dx);
                const force = (forceDist - dist) / forceDist;
                const pushStrength = 2; // how strong the repulsion is

                this.vx -= Math.cos(angle) * force * pushStrength * 0.05;
                this.vy -= Math.sin(angle) * force * pushStrength * 0.05;
            }
        }

        draw() {
            ctx.beginPath();
            ctx.arc(this.x, this.y, this.size, 0, Math.PI * 2);

            // Check body theme for color logic
            if (document.body.classList.contains('dark-theme')) {
                // Glowy particles in dark mode
                ctx.fillStyle = `rgba(161, 66, 244, ${this.baseAlpha})`; // Purpleish
            } else {
                // Subtle grey/blue in light mode
                ctx.fillStyle = `rgba(66, 133, 244, ${this.baseAlpha * 1.2})`; // Blueish
            }

            ctx.fill();
        }
    }

    function initParticles() {
        particles = [];
        const count = Math.floor((width * height) / 15000); // Density
        for (let i = 0; i < count; i++) {
            particles.push(new Particle());
        }
    }

    function animate() {
        ctx.clearRect(0, 0, width, height);

        particles.forEach(p => {
            p.update();
            p.draw();
        });

        requestAnimationFrame(animate);
    }

    // Init
    resize();
    animate();


    /* ----------------------------------------------------
       TAVUS CEO INTERACTION
    ---------------------------------------------------- */
    // The previous interactive demo has been replaced by a live Tavus interaction.
});

async function startCeoSession() {
    const btn = document.getElementById('ceo-connect-btn');
    const overlay = document.getElementById('ceo-overlay');
    const iframeContainer = document.getElementById('ceo-iframe-container');
    const originalText = btn.textContent;

    btn.textContent = 'Connecting...';
    btn.disabled = true;

    try {
        const response = await fetch('/api/start-tutor-session', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ tutorId: 'ceo' })
        });

        const data = await response.json();
        if (data.error) throw new Error(data.error);

        overlay.style.display = 'none';
        iframeContainer.style.display = 'block';
        iframeContainer.innerHTML = `<iframe src="${data.conversation_url}" allow="camera; microphone; autoplay; display-capture; fullscreen" style="width:100%; height:100%; border:none;"></iframe>`;

        // Optional: End trial after 2.5 minutes
        setTimeout(() => {
            iframeContainer.innerHTML = '<div style="color:white; text-align:center; padding-top:200px;">Trial session ended. <br><a href="signup.html" style="color:#4285F4;">Sign up</a> for full access.</div>';
        }, 150000);

    } catch (err) {
        console.error(err);
        alert("Failed to connect: " + err.message);
        btn.textContent = originalText;
        btn.disabled = false;
    }
}

/* ----------------------------------------------------
   VIDEO SOUND TOGGLE
---------------------------------------------------- */
function toggleVideoSound(video) {
    if (video.muted) {
        video.muted = false;
        video.volume = 1.0;
    } else {
        video.muted = true;
    }
}

// Custom video controls removed (unused)
