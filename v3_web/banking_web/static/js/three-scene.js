(function() {
    if (typeof THREE === 'undefined') return;

    var scene = new THREE.Scene();
    scene.background = null;

    var camera = new THREE.PerspectiveCamera(45, window.innerWidth / window.innerHeight, 0.1, 1000);
    camera.position.set(8, 5, 12);
    camera.lookAt(0, 0, 0);

    var renderer = new THREE.WebGLRenderer({ alpha: true, antialias: true });
    renderer.setSize(window.innerWidth, window.innerHeight);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    renderer.shadowMap.enabled = true;
    renderer.shadowMap.type = THREE.PCFSoftShadowMap;
    renderer.toneMapping = THREE.ACESFilmicToneMapping;
    renderer.toneMappingExposure = 1.2;

    var canvas = renderer.domElement;
    canvas.style.position = 'fixed';
    canvas.style.top = '0';
    canvas.style.left = '0';
    canvas.style.width = '100%';
    canvas.style.height = '100%';
    canvas.style.zIndex = '0';
    canvas.style.pointerEvents = 'none';
    document.body.prepend(canvas);

    // Lights
    var ambientLight = new THREE.AmbientLight(0x404060, 0.5);
    scene.add(ambientLight);

    var dirLight = new THREE.DirectionalLight(0x818cf8, 1.5);
    dirLight.position.set(5, 10, 7);
    dirLight.castShadow = true;
    scene.add(dirLight);

    var fillLight = new THREE.DirectionalLight(0x67e8f9, 0.6);
    fillLight.position.set(-3, 2, 5);
    scene.add(fillLight);

    var rimLight = new THREE.DirectionalLight(0xa855f7, 0.4);
    rimLight.position.set(0, -2, -8);
    scene.add(rimLight);

    // --- Build ATM Machine ---
    var atmGroup = new THREE.Group();

    // Main body
    var bodyGeo = new THREE.BoxGeometry(2.2, 3.2, 1.6);
    var bodyMat = new THREE.MeshPhysicalMaterial({
        color: 0x1a1b3a,
        metalness: 0.6,
        roughness: 0.3,
        envMapIntensity: 0.5,
    });
    var body = new THREE.Mesh(bodyGeo, bodyMat);
    body.position.y = 1.6;
    body.castShadow = true;
    atmGroup.add(body);

    // Screen (glowing blue)
    var screenGeo = new THREE.BoxGeometry(1.6, 0.9, 0.05);
    var screenMat = new THREE.MeshPhysicalMaterial({
        color: 0x818cf8,
        emissive: 0x818cf8,
        emissiveIntensity: 0.5,
        transparent: true,
        opacity: 0.9,
    });
    var screen = new THREE.Mesh(screenGeo, screenMat);
    screen.position.set(0, 2.2, 0.85);
    atmGroup.add(screen);

    // Screen inner
    var innerScreenGeo = new THREE.BoxGeometry(1.4, 0.7, 0.06);
    var innerScreenMat = new THREE.MeshPhysicalMaterial({
color: 0x0d0d11,
  emissive: 0x0d0d11,
    });
    var innerScreen = new THREE.Mesh(innerScreenGeo, innerScreenMat);
    innerScreen.position.set(0, 2.2, 0.9);
    atmGroup.add(innerScreen);

    // Keypad area
    var keypadGeo = new THREE.BoxGeometry(1.2, 0.8, 0.05);
    var keypadMat = new THREE.MeshPhysicalMaterial({
        color: 0x14143a,
        metalness: 0.3,
        roughness: 0.7,
    });
    var keypad = new THREE.Mesh(keypadGeo, keypadMat);
    keypad.position.set(0, 1.0, 0.85);
    atmGroup.add(keypad);

    // Keypad buttons (4x3 grid)
    var btnMat = new THREE.MeshPhysicalMaterial({
        color: 0x818cf8,
        emissive: 0x818cf8,
        emissiveIntensity: 0.15,
        transparent: true,
        opacity: 0.8,
    });
    for (var row = 0; row < 4; row++) {
        for (var col = 0; col < 3; col++) {
            var btn = new THREE.Mesh(new THREE.SphereGeometry(0.06, 8, 8), btnMat);
            btn.position.set(-0.4 + col * 0.4, 1.0 - row * 0.18 + 0.27, 0.9);
            atmGroup.add(btn);
        }
    }

    // Card slot
    var slotGeo = new THREE.BoxGeometry(0.3, 0.04, 0.15);
    var slotMat = new THREE.MeshPhysicalMaterial({ color: 0x2a2a4a });
    var slot = new THREE.Mesh(slotGeo, slotMat);
    slot.position.set(0.5, 0.5, 0.85);
    atmGroup.add(slot);

    // Cash dispenser slot
    var cashGeo = new THREE.BoxGeometry(0.8, 0.04, 0.15);
    var cashMat = new THREE.MeshPhysicalMaterial({ color: 0x1e1e3a });
    var cash = new THREE.Mesh(cashGeo, cashMat);
    cash.position.set(0, 0.3, 0.85);
    atmGroup.add(cash);

    // Glow strip around screen
    var stripMat = new THREE.MeshPhysicalMaterial({
        color: 0x818cf8,
        emissive: 0x818cf8,
        emissiveIntensity: 0.2,
        transparent: true,
        opacity: 0.6,
    });
    var strip = new THREE.Mesh(new THREE.BoxGeometry(1.7, 0.02, 0.02), stripMat);
    strip.position.set(0, 2.65, 0.85);
    atmGroup.add(strip);
    var strip2 = new THREE.Mesh(new THREE.BoxGeometry(1.7, 0.02, 0.02), stripMat);
    strip2.position.set(0, 1.75, 0.85);
    atmGroup.add(strip2);

    // Brand label
    var brandGeo = new THREE.BoxGeometry(0.6, 0.12, 0.02);
    var brandMat = new THREE.MeshPhysicalMaterial({
        color: 0x818cf8,
        emissive: 0x818cf8,
        emissiveIntensity: 0.3,
    });
    var brand = new THREE.Mesh(brandGeo, brandMat);
    brand.position.set(0, 0.1, 0.85);
    atmGroup.add(brand);

    scene.add(atmGroup);

    // --- Floating Particles ---
    var particleCount = 200;
    var particleGeo = new THREE.BufferGeometry();
    var positions = new Float32Array(particleCount * 3);
    var colors = new Float32Array(particleCount * 3);
    var sizes = new Float32Array(particleCount);

    for (var i = 0; i < particleCount; i++) {
        positions[i * 3] = (Math.random() - 0.5) * 30;
        positions[i * 3 + 1] = (Math.random() - 0.5) * 20;
        positions[i * 3 + 2] = (Math.random() - 0.5) * 20 - 5;

        var c = new THREE.Color();
        c.setHSL(0.58 + Math.random() * 0.08, 0.6, 0.5 + Math.random() * 0.3);
        colors[i * 3] = c.r;
        colors[i * 3 + 1] = c.g;
        colors[i * 3 + 2] = c.b;

        sizes[i] = 0.02 + Math.random() * 0.06;
    }

    particleGeo.setAttribute('position', new THREE.BufferAttribute(positions, 3));
    particleGeo.setAttribute('color', new THREE.BufferAttribute(colors, 3));
    particleGeo.setAttribute('size', new THREE.BufferAttribute(sizes, 1));

    var particleMat = new THREE.PointsMaterial({
        size: 0.06,
        vertexColors: true,
        transparent: true,
        opacity: 0.6,
        blending: THREE.AdditiveBlending,
        sizeAttenuation: true,
    });
    var particles = new THREE.Points(particleGeo, particleMat);
    scene.add(particles);

    // Ground grid
    var gridHelper = new THREE.GridHelper(20, 20, 0x818cf8, 0x1a2a4a);
    gridHelper.position.y = -0.2;
    gridHelper.material.transparent = true;
    gridHelper.material.opacity = 0.15;
    scene.add(gridHelper);

    // --- Mouse tracking ---
    var mouseX = 0, mouseY = 0;
    document.addEventListener('mousemove', function(e) {
        mouseX = (e.clientX / window.innerWidth) * 2 - 1;
        mouseY = -(e.clientY / window.innerHeight) * 2 + 1;
    });

    // --- Resize handler ---
    window.addEventListener('resize', function() {
        camera.aspect = window.innerWidth / window.innerHeight;
        camera.updateProjectionMatrix();
        renderer.setSize(window.innerWidth, window.innerHeight);
    });

    // --- Animation loop (pausable, reduced-motion aware) ---
    var clock = new THREE.Clock();
    var running = true;
    var reducedMotion = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;

    if (reducedMotion) {
        running = false;
        renderer.render(scene, camera);
    } else {
        var canvasEl = renderer.domElement;
        var io = new IntersectionObserver(function (entries) {
            running = entries[0].isIntersecting;
            if (running) clock.getDelta();
        }, { threshold: 0.02 });
        io.observe(canvasEl);
        document.addEventListener('visibilitychange', function () {
            if (document.hidden) running = false;
            if (!document.hidden) { running = true; clock.getDelta(); }
        });
    }

    function animate() {
        requestAnimationFrame(animate);
        if (!running) return;
        var t = clock.getElapsedTime();

        // Float the ATM gently
        atmGroup.position.y = Math.sin(t * 0.3) * 0.1;
        atmGroup.rotation.y = Math.sin(t * 0.15) * 0.05;

        // Particles drift
        var pos = particles.geometry.attributes.position.array;
        for (var i = 0; i < particleCount; i++) {
            pos[i * 3 + 1] += Math.sin(t + i) * 0.0005;
            pos[i * 3] += Math.cos(t * 0.2 + i * 0.1) * 0.0003;
        }
        particles.geometry.attributes.position.needsUpdate = true;

        // Pulse screen glow
        var pulse = 0.3 + Math.sin(t * 1.5) * 0.2;
        screenMat.emissiveIntensity = pulse;

        // Camera movement based on mouse
        camera.position.x = 8 + mouseX * 2;
        camera.position.y = 5 + mouseY * 1;
        camera.lookAt(0, 1.5, 0);

        renderer.render(scene, camera);
    }
    animate();
})();
