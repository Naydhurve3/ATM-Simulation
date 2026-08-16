(function() {
    var canvas = document.createElement('canvas');
    canvas.style.position = 'fixed';
    canvas.style.top = '0';
    canvas.style.left = '0';
    canvas.style.width = '100%';
    canvas.style.height = '100%';
    canvas.style.zIndex = '9999';
    canvas.style.pointerEvents = 'none';
    document.body.appendChild(canvas);

    var ctx = canvas.getContext('2d');
    var width, height;
    var particles = [];
    var mouse = { x: 0, y: 0 };

    function resize() {
        width = window.innerWidth;
        height = window.innerHeight;
        canvas.width = width;
        canvas.height = height;
    }
    resize();
    window.addEventListener('resize', resize);

    document.addEventListener('mousemove', function(e) {
        mouse.x = e.clientX;
        mouse.y = e.clientY;
        for (var i = 0; i < 2; i++) {
            particles.push({
                x: mouse.x + (Math.random() - 0.5) * 10,
                y: mouse.y + (Math.random() - 0.5) * 10,
                vx: (Math.random() - 0.5) * 0.5,
                vy: (Math.random() - 0.5) * 0.5,
                life: 1,
                maxLife: 0.6 + Math.random() * 0.6,
                size: 2 + Math.random() * 3,
                hue: (Math.random() < 0.15 ? 160 : 232) + Math.random() * 26,
            });
        }
    });

    function animate() {
        requestAnimationFrame(animate);
        ctx.clearRect(0, 0, width, height);

        for (var i = particles.length - 1; i >= 0; i--) {
            var p = particles[i];
            p.x += p.vx;
            p.y += p.vy;
            p.life -= 1 / (p.maxLife * 60);

            if (p.life <= 0) {
                particles.splice(i, 1);
                continue;
            }

            var alpha = p.life * 0.5;
            ctx.beginPath();
            ctx.arc(p.x, p.y, p.size * p.life, 0, Math.PI * 2);
            ctx.fillStyle = 'hsla(' + p.hue + ', 80%, 60%, ' + alpha + ')';
            ctx.fill();
        }

        if (particles.length > 100) {
            particles.splice(0, particles.length - 100);
        }
    }
    animate();
})();
