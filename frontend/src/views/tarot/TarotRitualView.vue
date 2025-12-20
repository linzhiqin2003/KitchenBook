<template>
  <div class="min-h-screen bg-mystic-dark text-mystic-gold p-4 flex flex-col items-center overflow-hidden relative font-mystic">
    <!-- Animated Starfield Background -->
    <StarField />

    <div class="relative z-10 w-full max-w-6xl flex flex-col items-center">
        <div class="text-center my-6">
            <h2 class="text-3xl mb-2 tracking-widest uppercase glow-text">The Ritual</h2>
            <p class="text-gray-400 text-sm italic h-6">{{ stepHint }}</p>
        </div>

        <!-- Main content container with proper sizing -->
        <div class="w-full min-h-[600px] flex flex-col items-center justify-start pt-4">
            <!-- Step 0: Select Spread -->
            <transition name="smooth" mode="out-in">
                <div v-if="step === 'spread'" key="spread" class="w-full flex flex-col items-center">
                    <h3 class="text-lg text-gray-300 mb-6">Choose Your Spread</h3>
                    <SpreadSelector :spreads="spreads" @select="selectSpread" />
                </div>

                <!-- Step 1: Input Question -->
                <div v-else-if="step === 'input'" key="input" class="w-full max-w-xl flex flex-col items-center pt-8">
                    <div class="mb-4 text-center">
                        <span class="text-mystic-purple text-sm">{{ selectedSpread?.name_cn }}</span>
                        <span class="text-gray-500 text-xs ml-2">({{ selectedSpread?.card_count }} cards)</span>
                    </div>
                    <input 
                        v-model="question" 
                        type="text" 
                        placeholder="What does the universe hold for me?"
                        class="w-full bg-transparent border-b-2 border-mystic-gold p-4 text-2xl focus:outline-none text-center placeholder-gray-600 transition-colors focus:border-mystic-purple"
                        @keydown.enter="handleEnter"
                        @compositionstart="isComposing = true"
                        @compositionend="isComposing = false"
                    />
                    <div class="flex gap-4 mt-12">
                        <button @click="step = 'spread'" class="px-6 py-2 border border-gray-600 text-gray-400 hover:border-mystic-gold hover:text-mystic-gold transition-all">
                            ← Back
                        </button>
                        <button 
                            @click="startShuffle"
                            :disabled="!question"
                            class="px-10 py-3 border border-mystic-gold hover:bg-mystic-gold hover:text-black transition-all duration-500 uppercase tracking-widest disabled:opacity-50 disabled:cursor-not-allowed group"
                        >
                            <span class="group-hover:tracking-[0.2em] transition-all">Begin Divination</span>
                        </button>
                    </div>
                </div>

                <!-- Step 2: Shuffle Animation -->
                <div v-else-if="step === 'shuffle'" key="shuffle" class="w-full h-80 flex items-center justify-center relative">
                    <div class="relative w-48 h-72">
                        <div 
                            v-for="(card, index) in shuffledDeck.slice(0, 15)" 
                            :key="card.id"
                            class="absolute w-full h-full bg-mystic-dark border border-mystic-gold rounded-xl shadow-2xl transition-all duration-300"
                            :style="getShuffleStyle(index)"
                        >
                            <div class="absolute inset-0 flex items-center justify-center text-3xl text-mystic-gold opacity-30">✧</div>
                        </div>
                    </div>
                    <div class="absolute bottom-0 text-mystic-purple animate-pulse tracking-widest uppercase text-sm">Shuffling the Arcana...</div>
                </div>

                <!-- Step 3: Pick Cards - Horizontal Deck on Table -->
                <div v-else-if="step === 'pick'" key="pick" class="w-full flex flex-col items-center">
                    <!-- Tarot Table Scene - Responsive -->
                    <div class="relative w-full h-[320px] sm:h-[380px] md:h-[450px] rounded-2xl md:rounded-3xl overflow-hidden">
                        <!-- Table Background with feathered edges -->
                        <img src="/tarot-table-bg.png" alt="" class="absolute inset-0 w-full h-full object-cover" />
                        <!-- Vignette overlay for soft edges -->
                        <div class="absolute inset-0 vignette-overlay"></div>
                        <div class="absolute inset-0 bg-gradient-to-t from-mystic-dark via-transparent to-mystic-dark/50"></div>
                        <div class="absolute inset-0 bg-gradient-to-r from-mystic-dark/60 via-transparent to-mystic-dark/60"></div>
                        
                        <!-- Instruction -->
                        <div class="absolute top-4 sm:top-6 left-0 right-0 text-center z-20">
                            <span class="text-mystic-gold text-base sm:text-xl drop-shadow-lg bg-black/50 px-4 sm:px-6 py-1.5 sm:py-2 rounded-full">
                                Select {{ remainingPicks }} card{{ remainingPicks > 1 ? 's' : '' }}
                            </span>
                        </div>
                        
                        <!-- Horizontal Card Deck - Responsive -->
                        <div class="absolute bottom-8 sm:bottom-12 left-0 right-0 flex justify-center overflow-visible px-2">
                            <div class="relative w-full" :style="{ maxWidth: containerWidth + 'px', height: isMobile ? '100px' : '140px' }">
                                <div 
                                    v-for="(card, index) in shuffledDeck.slice(0, displayCardCount)" 
                                    :key="card.id"
                                    @click="pickCard(index)"
                                    class="deck-card absolute cursor-pointer transition-all duration-300 hover:z-[100]"
                                    :class="[
                                        isMobile ? 'w-10 h-14 hover:-translate-y-4 hover:scale-115' : 'w-14 h-20 md:w-16 md:h-24 hover:-translate-y-8 hover:scale-125',
                                        pickedIndices.has(index) ? 'card-fly-out pointer-events-none' : '',
                                        cardsRevealed ? 'card-slide-in' : 'opacity-0'
                                    ]"
                                    :style="getHorizontalStyle(index)"
                                >
                                    <div class="w-full h-full bg-gradient-to-br from-indigo-950 via-purple-900 to-black border border-mystic-gold md:border-2 rounded-md md:rounded-lg shadow-xl md:shadow-2xl hover:border-white hover:shadow-mystic-gold/80 transition-all duration-200">
                                        <div class="absolute inset-0 flex items-center justify-center text-sm md:text-lg text-mystic-gold opacity-60">✧</div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                    
                    <!-- Selected Cards Preview - Responsive -->
                    <transition-group 
                        name="selected-card" 
                        tag="div" 
                        class="flex justify-center flex-wrap gap-3 sm:gap-6 mt-4 sm:mt-6 px-2"
                        v-if="drawnCards.length > 0"
                    >
                        <div 
                            v-for="(readingCard, index) in drawnCards" 
                            :key="readingCard.deckIndex"
                            @click="undoCardSelection(index)"
                            class="text-center cursor-pointer group"
                        >
                            <span class="text-mystic-purple text-xs block mb-1 sm:mb-2 font-medium truncate max-w-[60px] sm:max-w-none">{{ selectedSpread?.positions[index] }}</span>
                            <div class="w-12 h-18 sm:w-16 sm:h-24 bg-gradient-to-br from-indigo-950 via-purple-900 to-black border-2 border-mystic-gold rounded-lg flex items-center justify-center text-mystic-gold transition-all duration-300 group-hover:border-red-500 group-hover:scale-110 group-hover:rotate-3 shadow-lg group-hover:shadow-red-500/30">
                                <span class="text-lg sm:text-2xl group-hover:hidden">✧</span>
                                <span class="hidden group-hover:block text-base sm:text-xl">✕</span>
                            </div>
                            <span class="text-gray-500 text-xs mt-1 sm:mt-2 block opacity-0 group-hover:opacity-100 transition-opacity">撤销</span>
                        </div>
                    </transition-group>
                </div>
                
                <!-- Step 4: Reveal -->
                <div v-else-if="step === 'reveal'" key="reveal" class="w-full flex flex-col items-center">
                    <div :class="gridClass" class="gap-6 mb-12">
                        <div 
                            v-for="(readingCard, index) in drawnCards" 
                            :key="index" 
                            class="flex flex-col items-center gap-2"
                        >
                            <span class="text-gray-500 uppercase text-xs tracking-widest text-center">
                                {{ selectedSpread?.positions[index] || `Card ${index + 1}` }}
                            </span>
                            <TarotCard 
                                :card="readingCard.card" 
                                :revealed="readingCard.revealed"
                                @click="revealCard(index)"
                            />
                        </div>
                    </div>
                    
                    <!-- Interpretation Section -->
                    <div v-if="allRevealed" class="max-w-2xl text-center bg-black bg-opacity-50 p-8 rounded-xl border border-gray-800 animate-fade-in-up">
                        <h3 class="text-xl text-mystic-gold mb-4">Interpretation</h3>
                        
                        <div v-if="loadingAI" class="text-mystic-purple animate-pulse mb-4">
                            Consulting the Oracle...
                        </div>
                        <div v-else-if="aiInterpretation">
                            <p class="text-gray-300 leading-relaxed mb-6 whitespace-pre-line text-sm">{{ aiInterpretation }}</p>
                            
                            <!-- Simple Summary Section -->
                            <div v-if="aiSummary" class="mt-6 pt-6 border-t border-mystic-gold/30">
                                <h4 class="text-lg text-mystic-gold mb-3 flex items-center justify-center gap-2 font-chinese-title">
                                    <span>✨</span>
                                    <span>简明总结</span>
                                    <span>✨</span>
                                </h4>
                                <p class="text-white leading-loose text-base bg-gradient-to-r from-mystic-purple/20 via-mystic-gold/10 to-mystic-purple/20 p-5 rounded-lg font-chinese-body">
                                    {{ aiSummary }}
                                </p>
                            </div>
                        </div>
                        
                        <!-- Collapsible Card Details -->
                        <button 
                            @click="showCardDetails = !showCardDetails"
                            class="text-xs text-gray-500 hover:text-mystic-gold transition-colors flex items-center gap-2 mx-auto mt-6"
                        >
                            <span>{{ showCardDetails ? '▼' : '▶' }}</span>
                            <span>{{ showCardDetails ? 'Hide' : 'Show' }} Card Details</span>
                        </button>
                        
                        <transition name="slide">
                            <div v-if="showCardDetails" class="mt-4 text-left space-y-4 max-h-80 overflow-y-auto border-t border-gray-700 pt-4">
                                <div v-for="(readingCard, index) in drawnCards" :key="index" class="text-sm bg-black/30 p-3 rounded-lg">
                                    <div class="flex items-center gap-2 mb-2">
                                        <strong class="text-mystic-purple">{{ selectedSpread?.positions[index] }}:</strong>
                                        <span class="text-mystic-gold">{{ readingCard.card.name }}</span>
                                    </div>
                                    <!-- Keywords -->
                                    <div v-if="readingCard.card.keywords?.length" class="flex flex-wrap gap-1 mb-2">
                                        <span v-for="(kw, ki) in readingCard.card.keywords" :key="ki" 
                                            class="px-2 py-0.5 bg-mystic-purple/20 text-mystic-purple text-xs rounded">
                                            {{ kw }}
                                        </span>
                                    </div>
                                    <!-- Fortune Telling -->
                                    <p v-if="readingCard.card.fortune_telling?.length" class="text-gray-400 text-xs leading-relaxed">
                                        ✨ {{ readingCard.card.fortune_telling.join(' • ') }}
                                    </p>
                                </div>
                            </div>
                        </transition>
                        
                        <!-- Export Links - Only show when interpretation is ready -->
                        <div v-if="aiInterpretation && !loadingAI" class="mt-8 pt-4 border-t border-gray-800">
                            <div class="flex items-center justify-center gap-6 text-sm">
                                <button 
                                    @click="exportAsImage" 
                                    :disabled="exporting"
                                    class="text-gray-500 hover:text-mystic-gold transition-colors flex items-center gap-1.5 disabled:opacity-50"
                                >
                                    <span v-if="exporting" class="animate-spin">⏳</span>
                                    <span v-else>📷</span>
                                    <span class="font-chinese-body">{{ exporting ? '生成中...' : '保存图片' }}</span>
                                </button>
                                <span class="text-gray-700">|</span>
                                <button 
                                    @click="exportAsText" 
                                    class="text-gray-500 hover:text-mystic-gold transition-colors flex items-center gap-1.5"
                                >
                                    <span>📄</span>
                                    <span class="font-chinese-body">保存文本</span>
                                </button>
                            </div>
                        </div>
                        
                        <button @click="reset" class="mt-6 text-sm text-gray-500 hover:text-white underline decoration-mystic-purple font-chinese-body">再问一次</button>
                    </div>
                </div>
            </transition>
        </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, computed } from 'vue';
import html2canvas from 'html2canvas';
import FileSaver from 'file-saver';
import api from '../../api/tarot';
import TarotCard from '../../components/tarot/TarotCard.vue';
import SpreadSelector from '../../components/tarot/SpreadSelector.vue';
import StarField from '../../components/tarot/StarField.vue';

const step = ref('spread'); // spread, input, shuffle, pick, reveal
const question = ref('');
const deck = ref([]);
const shuffledDeck = ref([]);
const spreads = ref([]);
const selectedSpread = ref(null);
const drawnCards = ref([]);
const pickedIndices = ref(new Set());
const shuffleTick = ref(0);
const aiInterpretation = ref('');
const aiSummary = ref(''); // Simple Chinese summary
const loadingAI = ref(false);
const showCardDetails = ref(false);
const exporting = ref(false); // For export loading state
const isComposing = ref(false); // For IME input handling
const cardsRevealed = ref(false); // For spread animation

// Responsive layout detection
const isMobile = ref(false);
const containerWidth = ref(900);

const updateLayout = () => {
    const width = window.innerWidth;
    isMobile.value = width < 768;
    // Container width: min 320px, max 900px, with padding
    containerWidth.value = Math.min(900, Math.max(300, width - 32));
};

onMounted(async () => {
    updateLayout();
    window.addEventListener('resize', updateLayout);
    
    try {
        const [cardsRes, spreadsRes] = await Promise.all([
            api.getCards(),
            api.getSpreads()
        ]);
        deck.value = cardsRes.data;
        spreads.value = spreadsRes.data;
    } catch (e) {
        console.error("Failed to load data", e);
    }
});

onUnmounted(() => {
    window.removeEventListener('resize', updateLayout);
});

// Always show all cards, adjust spacing to fit
const displayCardCount = computed(() => {
    return shuffledDeck.value.length; // Always show all 78 cards
});

const stepHint = computed(() => {
    switch(step.value) {
        case 'spread': return 'Select a divination method...';
        case 'input': return 'Focus on your question...';
        case 'shuffle': return '';
        case 'pick': return 'Trust your intuition, choose wisely...';
        case 'reveal': return 'Click each card to reveal its wisdom...';
        default: return '';
    }
});

const remainingPicks = computed(() => {
    const total = selectedSpread.value?.card_count || 3;
    return total - drawnCards.value.length;
});

const gridClass = computed(() => {
    const count = selectedSpread.value?.card_count || 3;
    if (count === 1) return 'flex justify-center';
    if (count === 3) return 'flex flex-row justify-center flex-wrap'; // Always horizontal for 3 cards
    if (count === 5) return 'grid grid-cols-3 sm:grid-cols-5 place-items-center';
    if (count === 6) return 'grid grid-cols-3 place-items-center';
    if (count >= 10) return 'grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-5';
    return 'flex flex-row justify-center flex-wrap';
});

function selectSpread(spread) {
    selectedSpread.value = spread;
    step.value = 'input';
}

// Handle Enter key - ignore if IME is composing
function handleEnter(e) {
    if (isComposing.value || e.isComposing) return;
    startShuffle();
}

function shuffleDeck() {
    const arr = [...deck.value];
    for (let i = arr.length - 1; i > 0; i--) {
        const j = Math.floor(Math.random() * (i + 1));
        [arr[i], arr[j]] = [arr[j], arr[i]];
    }
    shuffledDeck.value = arr;
}

function getShuffleStyle(index) {
    const offset = Math.sin(shuffleTick.value + index * 0.5) * 30;
    const rotate = Math.cos(shuffleTick.value + index * 0.3) * 15;
    return {
        transform: `translateX(${offset}px) rotate(${rotate}deg)`,
        zIndex: 15 - index
    };
}

function getHorizontalStyle(index) {
    const total = displayCardCount.value || 78;
    const mobile = isMobile.value;
    const cWidth = containerWidth.value;
    
    // Card size based on screen
    const cardWidth = mobile ? 40 : 64; // w-10 or w-16
    
    // Calculate overlap to fit all cards in container
    // Formula: containerWidth = (total - 1) * overlap + cardWidth
    // So: overlap = (containerWidth - cardWidth) / (total - 1)
    const maxOverlap = mobile ? 8 : 12;
    const minOverlap = 3; // Minimum visible per card
    const calculatedOverlap = (cWidth - cardWidth - 20) / (total - 1); // 20px padding
    const overlap = Math.max(minOverlap, Math.min(maxOverlap, calculatedOverlap));
    
    const totalWidth = (total - 1) * overlap + cardWidth;
    const centerOffset = Math.max(10, (cWidth - totalWidth) / 2);
    const xPos = centerOffset + index * overlap;
    const startDelay = index * 0.006;
    
    // Slight arc effect for realism (reduced for tighter stacking)
    const centerIndex = total / 2;
    const distFromCenter = Math.abs(index - centerIndex);
    const arcHeight = Math.pow(distFromCenter, 1.3) * (mobile ? 0.05 : 0.1);
    const rotation = (index - centerIndex) * (mobile ? 0.15 : 0.25);
    
    return {
        left: `${xPos}px`,
        transform: `translateY(${arcHeight}px) rotate(${rotation}deg)`,
        zIndex: index,
        animationDelay: `${startDelay}s`
    };
}

function startShuffle() {
    if (!question.value || !selectedSpread.value) return;
    
    shuffleDeck();
    cardsRevealed.value = false;
    step.value = 'shuffle';
    
    const interval = setInterval(() => {
        shuffleTick.value += 0.4;
    }, 50);
    
    setTimeout(() => {
        clearInterval(interval);
        step.value = 'pick';
        // Trigger spread animation
        setTimeout(() => {
            cardsRevealed.value = true;
        }, 100);
    }, 2500);
}

function pickCard(index) {
    if (pickedIndices.value.has(index)) return;
    if (remainingPicks.value <= 0) return;
    
    pickedIndices.value.add(index);
    drawnCards.value.push({
        card: shuffledDeck.value[index],
        deckIndex: index, // Store original deck index for undo
        revealed: false
    });
    
    if (remainingPicks.value <= 0) {
        setTimeout(() => {
            step.value = 'reveal';
        }, 500);
    }
}

function undoCardSelection(previewIndex) {
    const removedCard = drawnCards.value[previewIndex];
    if (removedCard && removedCard.deckIndex !== undefined) {
        pickedIndices.value.delete(removedCard.deckIndex);
    }
    drawnCards.value.splice(previewIndex, 1);
}

function revealCard(index) {
    drawnCards.value[index].revealed = true;
    if (drawnCards.value.every(c => c.revealed)) {
        getAIInterpretation();
    }
}

const allRevealed = computed(() => drawnCards.value.length > 0 && drawnCards.value.every(c => c.revealed));

async function getAIInterpretation() {
    loadingAI.value = true;
    try {
        const payloadCards = drawnCards.value.map((c, i) => ({
            name: c.card.name,
            position: selectedSpread.value?.positions[i] || `Position ${i+1}`,
            meaning: c.card.meanings_light[0]
        }));
        
        const response = await api.divine(question.value, payloadCards, selectedSpread.value?.name);
        aiInterpretation.value = response.data.interpretation;
        aiSummary.value = response.data.summary || '';
    } catch (e) {
        console.error("Oracle silent", e);
        aiInterpretation.value = "The oracle is silent today.";
        aiSummary.value = "神谕暂时无法显示，请稍后再试。";
    } finally {
        loadingAI.value = false;
    }
}

function reset() {
    step.value = 'spread';
    question.value = '';
    selectedSpread.value = null;
    shuffledDeck.value = [];
    drawnCards.value = [];
    pickedIndices.value = new Set();
    aiInterpretation.value = '';
    aiSummary.value = '';
    showCardDetails.value = false;
    cardsRevealed.value = false;
}

// Export reading as image
async function exportAsImage() {
    exporting.value = true;
    
    try {
        // Create a styled container for the export
        const exportDiv = document.createElement('div');
        exportDiv.id = 'tarot-export-container';
        exportDiv.style.cssText = `
            position: fixed;
            top: 0;
            left: -9999px;
            width: 700px;
            background: linear-gradient(135deg, #0a0a12 0%, #1a1a2e 50%, #0a0a12 100%);
            padding: 40px;
            font-family: 'Noto Serif SC', serif;
            color: white;
            z-index: 99999;
        `;
        
        const now = new Date();
        const dateStr = now.toLocaleDateString('zh-CN', { year: 'numeric', month: 'long', day: 'numeric' });
        
        // Escape any special characters in the text
        const escapeHtml = (text) => {
            const div = document.createElement('div');
            div.textContent = text || '';
            return div.innerHTML;
        };
        
        exportDiv.innerHTML = `
            <div style="text-align: center; margin-bottom: 30px;">
                <h1 style="font-family: 'Cinzel', serif; color: #ffd700; font-size: 28px; margin-bottom: 10px;">✨ Tarot Reading ✨</h1>
                <p style="color: #888; font-size: 14px;">${dateStr}</p>
            </div>
            
            <div style="background: rgba(0,0,0,0.3); border: 1px solid #333; padding: 20px; border-radius: 12px; margin-bottom: 20px;">
                <h3 style="color: #a855f7; font-size: 14px; margin-bottom: 10px;">问题 / Question</h3>
                <p style="color: #e5e7eb; font-size: 16px;">${escapeHtml(question.value) || '无'}</p>
            </div>
            
            <div style="background: rgba(0,0,0,0.3); border: 1px solid #333; padding: 20px; border-radius: 12px; margin-bottom: 20px;">
                <h3 style="color: #a855f7; font-size: 14px; margin-bottom: 15px;">牌阵 / Spread: ${escapeHtml(selectedSpread.value?.name_cn || selectedSpread.value?.name)}</h3>
                <div style="display: flex; flex-wrap: wrap; gap: 20px; justify-content: center;">
                    ${drawnCards.value.map((rc, i) => `
                        <div style="text-align: center; width: 120px;">
                            <div style="color: #888; font-size: 11px; margin-bottom: 8px; height: 30px; display: flex; align-items: center; justify-content: center;">${escapeHtml(selectedSpread.value?.positions[i])}</div>
                            <div style="width: 100px; height: 150px; margin: 0 auto 8px; border-radius: 8px; overflow: hidden; border: 2px solid #ffd700; box-shadow: 0 4px 12px rgba(0,0,0,0.5);">
                                <img src="${window.location.origin}/cards/${rc.card.img}" style="width: 100%; height: 100%; object-fit: cover;" crossorigin="anonymous" />
                            </div>
                            <div style="color: #ffd700; font-size: 12px; font-weight: bold;">${escapeHtml(rc.card.name)}</div>
                        </div>
                    `).join('')}
                </div>
            </div>
            
            <div style="background: rgba(0,0,0,0.3); border: 1px solid #333; padding: 20px; border-radius: 12px; margin-bottom: 20px;">
                <h3 style="color: #ffd700; font-size: 16px; margin-bottom: 15px; text-align: center;">Interpretation</h3>
                <p style="color: #d1d5db; font-size: 14px; line-height: 1.8; white-space: pre-line;">${escapeHtml(aiInterpretation.value)}</p>
            </div>
            
            ${aiSummary.value ? `
            <div style="background: linear-gradient(90deg, rgba(76,29,149,0.3), rgba(255,215,0,0.1), rgba(76,29,149,0.3)); border: 1px solid rgba(255,215,0,0.3); padding: 20px; border-radius: 12px;">
                <h3 style="color: #ffd700; font-size: 16px; margin-bottom: 15px; text-align: center; font-family: 'ZCOOL XiaoWei', serif;">✨ 简明总结 ✨</h3>
                <p style="color: white; font-size: 16px; line-height: 2; font-family: 'Noto Serif SC', serif;">${escapeHtml(aiSummary.value)}</p>
            </div>
            ` : ''}
            
            <div style="text-align: center; margin-top: 30px; padding-top: 20px; border-top: 1px solid #333;">
                <p style="color: #666; font-size: 12px;">Generated by Tarot Sanctum</p>
            </div>
        `;
        
        document.body.appendChild(exportDiv);
        
        // Wait for images and fonts to load
        const images = exportDiv.querySelectorAll('img');
        await Promise.all([
            // Wait for all images to load
            ...Array.from(images).map(img => 
                new Promise(resolve => {
                    if (img.complete) resolve();
                    else {
                        img.onload = resolve;
                        img.onerror = resolve; // Continue even if image fails
                    }
                })
            ),
            // Wait for rendering to complete
            new Promise(resolve => setTimeout(resolve, 1000))
        ]);
        
        const canvas = await html2canvas(exportDiv, {
            backgroundColor: '#0a0a12',
            scale: 2,
            useCORS: true,
            logging: false,
            allowTaint: true,
            width: 700,
            windowWidth: 700
        });
        
        document.body.removeChild(exportDiv);
        
        // Convert to blob and download using file-saver
        const filename = `tarot-reading-${now.getTime()}.png`;
        
        await new Promise((resolve, reject) => {
            canvas.toBlob((blob) => {
                if (blob) {
                    FileSaver.saveAs(blob, filename);
                    resolve();
                } else {
                    reject(new Error('Failed to create blob'));
                }
            }, 'image/png');
        });
        
    } catch (error) {
        console.error('Export failed:', error);
        
        // Cleanup if needed
        try {
            const exportDiv = document.getElementById('tarot-export-container');
            if (exportDiv) document.body.removeChild(exportDiv);
        } catch (e) {}
        
        alert('导出失败，请重试');
    } finally {
        exporting.value = false;
    }
}

// Export reading as text file
function exportAsText() {
    const now = new Date();
    const dateStr = now.toLocaleDateString('zh-CN', { year: 'numeric', month: 'long', day: 'numeric', hour: '2-digit', minute: '2-digit' });
    
    const cardList = drawnCards.value.map((rc, i) => 
        `  ${selectedSpread.value?.positions[i] || `位置${i+1}`}: ${rc.card.name}`
    ).join('\n');
    
    const content = `
═══════════════════════════════════════════════
           ✨ TAROT READING / 塔罗占卜 ✨
═══════════════════════════════════════════════

📅 日期: ${dateStr}

💭 问题 / Question:
${question.value || '无'}

🎴 牌阵 / Spread: ${selectedSpread.value?.name || ''}
${cardList}

═══════════════════════════════════════════════
                  INTERPRETATION
═══════════════════════════════════════════════

${aiInterpretation.value}

═══════════════════════════════════════════════
                    简明总结
═══════════════════════════════════════════════

${aiSummary.value || '无'}

───────────────────────────────────────────────
Generated by Tarot Sanctum
`.trim();
    
    const blob = new Blob([content], { type: 'text/plain;charset=utf-8' });
    FileSaver.saveAs(blob, `tarot-reading-${now.getTime()}.txt`);
}
</script>

<style scoped>
/* Smooth transition - fade with slight slide */
.smooth-enter-active {
    transition: all 0.4s ease-out;
}
.smooth-leave-active {
    transition: all 0.3s ease-in;
}
.smooth-enter-from {
    opacity: 0;
    transform: translateY(20px);
}
.smooth-leave-to {
    opacity: 0;
    transform: translateY(-10px);
}

.slide-enter-active, .slide-leave-active { transition: all 0.3s ease; }
.slide-enter-from, .slide-leave-to { opacity: 0; max-height: 0; }
.slide-enter-to, .slide-leave-from { opacity: 1; max-height: 300px; }

.perspective-1000 { perspective: 1000px; }
.animate-fade-in-up { animation: fadeInUp 0.6s ease-out forwards; }
.glow-text {
  text-shadow: 0 0 10px rgba(255, 215, 0, 0.5), 0 0 20px rgba(255, 215, 0, 0.3);
}

/* Card spread animation - slide in from left */
.card-spread-in {
    animation: spreadIn 0.8s ease-out forwards;
}

/* Card fan animation - rotate into position */
.card-fan-in {
    animation: fanIn 0.6s ease-out forwards;
}

@keyframes spreadIn {
    from {
        opacity: 0;
        transform: translateX(-50px) scale(0.8);
    }
    to {
        opacity: 1;
        transform: translateX(0) scale(1);
    }
}

@keyframes fanIn {
    from {
        opacity: 0;
        transform: rotate(0deg) scale(0.5);
    }
    to {
        opacity: 1;
    }
}

@keyframes fadeInUp {
    from { opacity: 0; transform: translateY(20px); }
    to { opacity: 1; transform: translateY(0); }
}

/* Card slide-in animation for horizontal deck */
.card-slide-in {
    animation: slideIn 0.5s ease-out forwards;
}

@keyframes slideIn {
    from {
        opacity: 0;
        transform: translateY(30px) scale(0.9);
    }
    to {
        opacity: 1;
        transform: translateY(0) scale(1);
    }
}

/* Vignette overlay for soft feathered edges */
.vignette-overlay {
    background: radial-gradient(ellipse at center, transparent 30%, rgba(13, 13, 31, 0.6) 70%, rgba(13, 13, 31, 0.95) 100%);
}

/* Card fly out animation when selected */
.card-fly-out {
    animation: flyOut 0.5s ease-out forwards;
    pointer-events: none;
}

@keyframes flyOut {
    0% {
        opacity: 1;
        transform: translateY(0) scale(1);
    }
    50% {
        opacity: 0.8;
        transform: translateY(-100px) scale(1.2);
    }
    100% {
        opacity: 0;
        transform: translateY(-200px) scale(0.5);
    }
}

/* Selected card transition group animations */
.selected-card-enter-active {
    animation: cardAppear 0.4s ease-out;
}
.selected-card-leave-active {
    animation: cardDisappear 0.3s ease-in;
}
.selected-card-move {
    transition: transform 0.3s ease;
}

@keyframes cardAppear {
    0% {
        opacity: 0;
        transform: translateY(-50px) scale(0.5);
    }
    60% {
        opacity: 1;
        transform: translateY(10px) scale(1.1);
    }
    100% {
        opacity: 1;
        transform: translateY(0) scale(1);
    }
}

@keyframes cardDisappear {
    0% {
        opacity: 1;
        transform: translateY(0) scale(1) rotate(0deg);
    }
    100% {
        opacity: 0;
        transform: translateY(50px) scale(0.5) rotate(15deg);
    }
}

/* Deck card hover glow effect */
.deck-card:hover {
    filter: drop-shadow(0 0 10px rgba(255, 215, 0, 0.6));
}
</style>
