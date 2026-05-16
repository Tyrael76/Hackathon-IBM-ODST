const glowBg = document.querySelector('.glow-background');

if (glowBg) {
    window.addEventListener('mousemove', (e) => {
        const { clientX, clientY } = e;
        
        // Actualiza las variables CSS con la posición exacta del mouse
        glowBg.style.setProperty('--mouse-x', `${clientX}px`);
        glowBg.style.setProperty('--mouse-y', `${clientY}px`);
    });

    // Opcional: Centrar la luz si el mouse sale de la pantalla
    window.addEventListener('mouseout', () => {
        glowBg.style.setProperty('--mouse-x', `50vw`);
        glowBg.style.setProperty('--mouse-y', `50vh`);
    });
}
const canvas = document.getElementById('bg-canvas');
const ctx = canvas.getContext('2d');

let particlesArray = [];
const particleCount = 120; // Incrementado para mayor densidad
const connectionDistance = 150; // Líneas más largas

const mouse = {
    x: null,
    y: null,
    radius: 250 // Área magnética del cursor mucho más grande
};

function resizeCanvas() {
    canvas.width = window.innerWidth;
    canvas.height = window.innerHeight;
}
window.addEventListener('resize', resizeCanvas);
resizeCanvas();

window.addEventListener('mousemove', (event) => {
    mouse.x = event.clientX;
    mouse.y = event.clientY;
});

window.addEventListener('mouseout', () => {
    mouse.x = null;
    mouse.y = null;
});

class Particle {
    constructor() {
        this.x = Math.random() * canvas.width;
        this.y = Math.random() * canvas.height;
        this.vx = (Math.random() - 0.5) * 0.8;
        this.vy = (Math.random() - 0.5) * 0.8;
        this.radius = Math.random() * 2.5 + 1.5; // Nodos más grandes
    }

    draw() {
        ctx.beginPath();
        ctx.arc(this.x, this.y, this.radius, 0, Math.PI * 2);
        // Azul luminoso con alta opacidad
        ctx.fillStyle = 'rgba(88, 166, 255, 0.9)'; 
        ctx.fill();
    }

    update() {
        this.x += this.vx;
        this.y += this.vy;

        if (this.x < 0 || this.x > canvas.width) this.vx = -this.vx;
        if (this.y < 0 || this.y > canvas.height) this.vy = -this.vy;

        if (mouse.x !== null && mouse.y !== null) {
            let dx = mouse.x - this.x;
            let dy = mouse.y - this.y;
            let distance = Math.sqrt(dx * dx + dy * dy);
            
            if (distance < mouse.radius) {
                // Fuerte atracción al ratón
                this.x += (dx / distance) * 0.8;
                this.y += (dy / distance) * 0.8;
            }
        }
    }
}

function init() {
    particlesArray = [];
    for (let i = 0; i < particleCount; i++) {
        particlesArray.push(new Particle());
    }
}

function drawLines() {
    for (let i = 0; i < particlesArray.length; i++) {
        for (let j = i + 1; j < particlesArray.length; j++) {
            let dx = particlesArray[i].x - particlesArray[j].x;
            let dy = particlesArray[i].y - particlesArray[j].y;
            let distance = Math.sqrt(dx * dx + dy * dy);

            if (distance < connectionDistance) {
                // Opacidad base de las líneas muy alta
                let alpha = (1 - distance / connectionDistance) * 0.5;
                ctx.strokeStyle = `rgba(88, 166, 255, ${alpha})`;
                ctx.lineWidth = 1.5;
                ctx.beginPath();
                ctx.moveTo(particlesArray[i].x, particlesArray[i].y);
                ctx.lineTo(particlesArray[j].x, particlesArray[j].y);
                ctx.stroke();
            }
        }

        // Conexión súper brillante hacia el ratón
        if (mouse.x !== null && mouse.y !== null) {
            let dxMouse = particlesArray[i].x - mouse.x;
            let dyMouse = particlesArray[i].y - mouse.y;
            let distMouse = Math.sqrt(dxMouse * dxMouse + dyMouse * dyMouse);

            if (distMouse < mouse.radius) {
                let alphaMouse = (1 - distMouse / mouse.radius) * 0.8; // Muy visible
                ctx.strokeStyle = `rgba(88, 166, 255, ${alphaMouse})`;
                ctx.lineWidth = 2; // Línea gruesa hacia el cursor
                ctx.beginPath();
                ctx.moveTo(particlesArray[i].x, particlesArray[i].y);
                ctx.lineTo(mouse.x, mouse.y);
                ctx.stroke();
            }
        }
    }
}

function animate() {
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    for (let i = 0; i < particlesArray.length; i++) {
        particlesArray[i].update();
        particlesArray[i].draw();
    }
    drawLines();
    requestAnimationFrame(animate);
}

init();
animate();