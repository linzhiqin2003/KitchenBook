<template>
  <div class="fixed inset-0 z-0 overflow-hidden pointer-events-none select-none bg-black">
    <!-- Gradient Blobs -->
    <div class="absolute top-[-10%] left-[-10%] w-[50%] h-[50%] rounded-full bg-blue-900/20 blur-[120px] animate-float-slow"></div>
    <div class="absolute bottom-[-10%] right-[-10%] w-[50%] h-[50%] rounded-full bg-purple-900/20 blur-[120px] animate-float-delayed"></div>
    <div class="absolute top-[20%] right-[20%] w-[30%] h-[30%] rounded-full bg-indigo-900/10 blur-[100px] animate-pulse-slow"></div>
  </div>
</template>

<style scoped>
@keyframes float {
  0%, 100% { transform: translate(0, 0); }
  33% { transform: translate(30px, -50px); }
  66% { transform: translate(-20px, 20px); }
}

.animate-float-slow {
  animation: float 20s infinite ease-in-out;
}

.animate-float-delayed {
  animation: float 25s infinite ease-in-out reverse;
}

.animate-pulse-slow {
  animation: pulse 10s infinite ease-in-out;
}
</style>
