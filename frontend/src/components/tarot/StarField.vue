<template>
  <canvas ref="canvas" class="fixed inset-0 z-0 pointer-events-none"></canvas>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue';

const canvas = ref(null);
let ctx = null;
let animationId = null;
let stars = [];
let shootingStars = [];

const config = {
  starCount: 200,
  starMinSize: 0.5,
  starMaxSize: 2,
  twinkleSpeed: 0.02,
  shootingStarChance: 0.002,
  colors: ['#ffd700', '#ffffff', '#a855f7', '#60a5fa']
};

class Star {
  constructor(width, height) {
    this.reset(width, height);
  }
  
  reset(width, height) {
    this.x = Math.random() * width;
    this.y = Math.random() * height;
    this.size = config.starMinSize + Math.random() * (config.starMaxSize - config.starMinSize);
    this.color = config.colors[Math.floor(Math.random() * config.colors.length)];
    this.alpha = Math.random();
    this.alphaDirection = Math.random() > 0.5 ? 1 : -1;
    this.speed = 0.005 + Math.random() * 0.015;
  }
  
  update() {
    this.alpha += this.alphaDirection * this.speed;
    if (this.alpha >= 1) {
      this.alpha = 1;
      this.alphaDirection = -1;
    } else if (this.alpha <= 0.2) {
      this.alpha = 0.2;
      this.alphaDirection = 1;
    }
  }
  
  draw(ctx) {
    ctx.beginPath();
    ctx.arc(this.x, this.y, this.size, 0, Math.PI * 2);
    ctx.fillStyle = this.color;
    ctx.globalAlpha = this.alpha;
    ctx.fill();
    ctx.globalAlpha = 1;
  }
}

class ShootingStar {
  constructor(width, height) {
    this.reset(width, height);
  }
  
  reset(width, height) {
    this.x = Math.random() * width;
    this.y = 0;
    this.length = 80 + Math.random() * 60;
    this.speed = 8 + Math.random() * 6;
    this.angle = Math.PI / 4 + (Math.random() - 0.5) * 0.3;
    this.opacity = 1;
    this.active = true;
  }
  
  update(height) {
    this.x += Math.cos(this.angle) * this.speed;
    this.y += Math.sin(this.angle) * this.speed;
    this.opacity -= 0.015;
    
    if (this.y > height || this.opacity <= 0) {
      this.active = false;
    }
  }
  
  draw(ctx) {
    if (!this.active) return;
    
    const tailX = this.x - Math.cos(this.angle) * this.length;
    const tailY = this.y - Math.sin(this.angle) * this.length;
    
    const gradient = ctx.createLinearGradient(tailX, tailY, this.x, this.y);
    gradient.addColorStop(0, 'rgba(255, 215, 0, 0)');
    gradient.addColorStop(1, `rgba(255, 215, 0, ${this.opacity})`);
    
    ctx.beginPath();
    ctx.moveTo(tailX, tailY);
    ctx.lineTo(this.x, this.y);
    ctx.strokeStyle = gradient;
    ctx.lineWidth = 2;
    ctx.stroke();
    
    // Glow at head
    ctx.beginPath();
    ctx.arc(this.x, this.y, 3, 0, Math.PI * 2);
    ctx.fillStyle = `rgba(255, 255, 255, ${this.opacity})`;
    ctx.fill();
  }
}

function init() {
  if (!canvas.value) return;
  
  ctx = canvas.value.getContext('2d');
  resizeCanvas();
  
  stars = [];
  for (let i = 0; i < config.starCount; i++) {
    stars.push(new Star(canvas.value.width, canvas.value.height));
  }
  
  animate();
}

function resizeCanvas() {
  if (!canvas.value) return;
  canvas.value.width = window.innerWidth;
  canvas.value.height = window.innerHeight;
}

function animate() {
  if (!ctx || !canvas.value) return;
  
  ctx.clearRect(0, 0, canvas.value.width, canvas.value.height);
  
  // Update and draw stars
  stars.forEach(star => {
    star.update();
    star.draw(ctx);
  });
  
  // Chance to create shooting star
  if (Math.random() < config.shootingStarChance) {
    shootingStars.push(new ShootingStar(canvas.value.width, canvas.value.height));
  }
  
  // Update and draw shooting stars
  shootingStars = shootingStars.filter(ss => ss.active);
  shootingStars.forEach(ss => {
    ss.update(canvas.value.height);
    ss.draw(ctx);
  });
  
  animationId = requestAnimationFrame(animate);
}

onMounted(() => {
  init();
  window.addEventListener('resize', resizeCanvas);
});

onUnmounted(() => {
  if (animationId) {
    cancelAnimationFrame(animationId);
  }
  window.removeEventListener('resize', resizeCanvas);
});
</script>
