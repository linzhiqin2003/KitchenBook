<template>
  <div class="ios-card p-6 md:p-8 animate-pulse">
    <!-- Topic Badge Skeleton -->
    <div class="flex items-center justify-between mb-6">
      <div class="flex items-center gap-2">
        <div class="h-6 w-24 bg-gray-200 rounded-full"></div>
        <div class="h-5 w-16 bg-gray-200 rounded-full"></div>
      </div>
      <div class="h-5 w-8 bg-gray-200 rounded"></div>
    </div>

    <!-- Question Text Skeleton -->
    <div class="space-y-3 mb-8">
      <div class="h-4 bg-gray-200 rounded w-full"></div>
      <div class="h-4 bg-gray-200 rounded w-11/12"></div>
      <div class="h-4 bg-gray-200 rounded w-4/5"></div>
    </div>

    <!-- Options Skeleton -->
    <div class="space-y-4 mb-8">
      <div v-for="i in 4" :key="i" class="skeleton-option">
        <div class="flex items-center gap-3 p-4">
          <div class="w-6 h-6 bg-gray-300 rounded-full flex-shrink-0"></div>
          <div class="flex-1 space-y-2">
            <div class="h-4 bg-gray-200 rounded w-3/4"></div>
          </div>
        </div>
      </div>
    </div>

    <!-- Button Skeleton -->
    <div class="pt-4 border-t border-gray-100">
      <div class="h-12 bg-gray-200 rounded-2xl w-full"></div>
    </div>
  </div>
</template>

<style scoped>
.skeleton-option {
  background: rgba(255, 255, 255, 0.6);
  border-radius: 16px;
  border: 2px solid transparent;
}

@keyframes shimmer {
  0% {
    background-position: -200% 0;
  }
  100% {
    background-position: 200% 0;
  }
}

.ios-card :deep(.bg-gray-200),
.ios-card :deep(.bg-gray-300) {
  background: linear-gradient(
    90deg,
    #e5e7eb 25%,
    #f3f4f6 50%,
    #e5e7eb 75%
  );
  background-size: 200% 100%;
  animation: shimmer 1.5s infinite;
}
</style>
