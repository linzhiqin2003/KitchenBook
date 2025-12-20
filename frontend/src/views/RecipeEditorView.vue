<script setup>
import { ref, onMounted, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import axios from 'axios'
import API_BASE_URL from '../config/api'

const route = useRoute()
const router = useRouter()
const isEdit = computed(() => route.params.id !== undefined)
const recipeId = computed(() => route.params.id)

// 基础信息表单
const form = ref({
    title: '',
    description: '',
    cooking_time: 30,
    category: '',
    is_public: true,
    chef_notes: '',
    cover_image: null 
})

// 步骤列表
const steps = ref([])

// 食材列表
const ingredients = ref([])

// 已有食材库（用于自动补全）
const ingredientLibrary = ref([])

const imagePreview = ref(null)
const loading = ref(false)
const saving = ref(false)
const activeTab = ref('basic') // 'basic' | 'steps' | 'ingredients'

// 加载数据
onMounted(async () => {
    // 加载食材库
    try {
        const { data } = await axios.get(`${API_BASE_URL}/api/ingredients/`)
        ingredientLibrary.value = data
    } catch (e) {
        console.error('加载食材库失败', e)
    }

    if (isEdit.value) {
        loading.value = true
        try {
            const { data } = await axios.get(`${API_BASE_URL}/api/recipes/${recipeId.value}/?mode=chef`)
            form.value = { 
                title: data.title || '',
                description: data.description || '',
                cooking_time: data.cooking_time || 30,
                category: data.category || '',
                is_public: data.is_public !== false,
                chef_notes: data.chef_notes || '',
                cover_image: null 
            }
            imagePreview.value = data.cover_image
            
            // 加载步骤
            if (data.steps && data.steps.length > 0) {
                steps.value = data.steps.map(s => ({
                    id: s.id,
                    step_number: s.step_number,
                    description: s.description,
                    image: s.image,
                    imageFile: null,
                    imagePreview: s.image
                }))
            }
            
            // 加载食材
            if (data.ingredients && data.ingredients.length > 0) {
                ingredients.value = data.ingredients.map(i => ({
                    id: i.id,
                    ingredient_name: i.ingredient_name,
                    quantity_display: i.quantity || ''
                }))
            }
        } catch (e) {
            alert('加载失败')
            router.push('/kitchen/chef/recipes')
        } finally {
            loading.value = false
        }
    }
})

// 封面图片上传
const handleFileUpload = (event) => {
    const file = event.target.files[0]
    if (file) {
        form.value.cover_image = file
        imagePreview.value = URL.createObjectURL(file)
    }
}

// ========== 步骤管理 ==========
const addStep = () => {
    const nextNumber = steps.value.length > 0 
        ? Math.max(...steps.value.map(s => s.step_number)) + 1 
        : 1
    steps.value.push({
        id: null,
        step_number: nextNumber,
        description: '',
        image: null,
        imageFile: null,
        imagePreview: null
    })
}

const removeStep = (index) => {
    steps.value.splice(index, 1)
    // 重新编号
    steps.value.forEach((s, i) => {
        s.step_number = i + 1
    })
}

const moveStep = (index, direction) => {
    const newIndex = index + direction
    if (newIndex < 0 || newIndex >= steps.value.length) return
    
    const temp = steps.value[index]
    steps.value[index] = steps.value[newIndex]
    steps.value[newIndex] = temp
    
    // 重新编号
    steps.value.forEach((s, i) => {
        s.step_number = i + 1
    })
}

const handleStepImageUpload = (event, index) => {
    const file = event.target.files[0]
    if (file) {
        steps.value[index].imageFile = file
        steps.value[index].imagePreview = URL.createObjectURL(file)
    }
}

// ========== 食材管理 ==========
const addIngredient = () => {
    ingredients.value.push({
        id: null,
        ingredient_name: '',
        quantity_display: ''
    })
}

const removeIngredient = (index) => {
    ingredients.value.splice(index, 1)
}

// 自动补全建议
const getIngredientSuggestions = (query) => {
    if (!query) return []
    return ingredientLibrary.value
        .filter(ing => ing.name.toLowerCase().includes(query.toLowerCase()))
        .slice(0, 5)
}

// ========== 保存 ==========
const submit = async () => {
    saving.value = true
    
    try {
        let currentRecipeId = recipeId.value
        
        // 1. 先保存基础信息
        const formData = new FormData()
        formData.append('title', form.value.title)
        formData.append('description', form.value.description || '')
        formData.append('cooking_time', form.value.cooking_time)
        formData.append('category', form.value.category || '')
        formData.append('is_public', form.value.is_public ? 'true' : 'false')
        formData.append('chef_notes', form.value.chef_notes || '')
        
        if (form.value.cover_image instanceof File) {
            formData.append('cover_image', form.value.cover_image)
        }

        if (isEdit.value) {
            await axios.patch(`${API_BASE_URL}/api/recipes/${currentRecipeId}/`, formData)
        } else {
            const { data } = await axios.post(`${API_BASE_URL}/api/recipes/`, formData)
            currentRecipeId = data.id
        }

        // 2. 保存步骤
        if (steps.value.length > 0) {
            // 批量更新步骤
            const stepsData = steps.value.map(s => ({
                id: s.id,
                step_number: s.step_number,
                description: s.description
            }))
            
            const { data: updatedSteps } = await axios.post(
                `${API_BASE_URL}/api/recipe-steps/batch-update/`, 
                { recipe_id: currentRecipeId, steps: stepsData }
            )
            
            // 上传步骤图片
            for (let i = 0; i < steps.value.length; i++) {
                if (steps.value[i].imageFile) {
                    const stepId = updatedSteps[i]?.id
                    if (stepId) {
                        const imgFormData = new FormData()
                        imgFormData.append('image', steps.value[i].imageFile)
                        await axios.post(
                            `${API_BASE_URL}/api/recipe-steps/${stepId}/upload-image/`,
                            imgFormData
                        )
                    }
                }
            }
        } else {
            // 清空所有步骤
            await axios.post(
                `${API_BASE_URL}/api/recipe-steps/batch-update/`, 
                { recipe_id: currentRecipeId, steps: [] }
            )
        }

        // 3. 保存食材
        const ingredientsData = ingredients.value
            .filter(i => i.ingredient_name.trim())
            .map(i => ({
                ingredient_name: i.ingredient_name.trim(),
                quantity_display: i.quantity_display || '',
                amount: 0
            }))
        
        await axios.post(
            `${API_BASE_URL}/api/recipe-ingredients/batch-update/`,
            { recipe_id: currentRecipeId, ingredients: ingredientsData }
        )

        router.push('/kitchen/chef/recipes')
    } catch (e) {
        console.error(e)
        alert('保存失败: ' + (e.response?.data?.detail || e.response?.data?.error || e.message))
    } finally {
        saving.value = false
    }
}
</script>

<template>
  <div class="min-h-screen bg-stone-50">
    <!-- Loading -->
    <div v-if="loading" class="flex items-center justify-center h-screen">
      <div class="text-center">
        <div class="text-4xl mb-4 animate-bounce">🍳</div>
        <p class="text-stone-500">正在加载菜谱...</p>
      </div>
    </div>

    <div v-else class="max-w-6xl mx-auto py-8 px-4">
      <!-- Header -->
      <div class="flex items-center justify-between mb-8">
        <div class="flex items-center gap-4">
          <router-link to="/kitchen/chef/recipes" class="w-10 h-10 flex items-center justify-center rounded-full bg-white border border-stone-200 text-stone-500 hover:bg-stone-50 transition-colors shadow-sm">
            ←
          </router-link>
          <div>
            <h1 class="text-2xl font-bold text-stone-800">{{ isEdit ? '编辑菜谱' : '新增菜谱' }}</h1>
            <p class="text-sm text-stone-500">完善您的美味杰作</p>
          </div>
        </div>
        <div class="flex gap-3">
          <button @click="router.push('/kitchen/chef/recipes')" class="px-4 py-2 rounded-lg text-stone-600 font-bold hover:bg-stone-100 transition-colors">
            取消
          </button>
          <button 
            @click="submit" 
            :disabled="saving"
            class="px-6 py-2 rounded-lg bg-emerald-600 text-white font-bold hover:bg-emerald-700 shadow-lg shadow-emerald-200 transition-all hover:-translate-y-0.5 flex items-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <span v-if="saving" class="animate-spin">⏳</span>
            <span v-else>💾</span>
            {{ saving ? '保存中...' : '保存更改' }}
          </button>
        </div>
      </div>

      <!-- Tab 导航 -->
      <div class="flex gap-2 mb-6 bg-white p-1 rounded-xl border border-stone-200 shadow-sm">
        <button 
          @click="activeTab = 'basic'"
          :class="[
            'flex-1 py-3 px-4 rounded-lg font-bold transition-all flex items-center justify-center gap-2',
            activeTab === 'basic' 
              ? 'bg-emerald-500 text-white shadow-md' 
              : 'text-stone-600 hover:bg-stone-50'
          ]"
        >
          <span>📝</span> 基础信息
        </button>
        <button 
          @click="activeTab = 'ingredients'"
          :class="[
            'flex-1 py-3 px-4 rounded-lg font-bold transition-all flex items-center justify-center gap-2',
            activeTab === 'ingredients' 
              ? 'bg-emerald-500 text-white shadow-md' 
              : 'text-stone-600 hover:bg-stone-50'
          ]"
        >
          <span>🥬</span> 食材清单
          <span v-if="ingredients.length" class="bg-white/20 px-2 py-0.5 rounded text-sm">{{ ingredients.length }}</span>
        </button>
        <button 
          @click="activeTab = 'steps'"
          :class="[
            'flex-1 py-3 px-4 rounded-lg font-bold transition-all flex items-center justify-center gap-2',
            activeTab === 'steps' 
              ? 'bg-emerald-500 text-white shadow-md' 
              : 'text-stone-600 hover:bg-stone-50'
          ]"
        >
          <span>👨‍🍳</span> 烹饪步骤
          <span v-if="steps.length" class="bg-white/20 px-2 py-0.5 rounded text-sm">{{ steps.length }}</span>
        </button>
      </div>

      <!-- Tab 内容 -->
      <Transition name="fade" mode="out-in">
        
        <!-- 基础信息 Tab -->
        <div v-if="activeTab === 'basic'" key="basic" class="grid grid-cols-1 lg:grid-cols-3 gap-8">
          <!-- Left Column: Image & Visibility -->
          <div class="space-y-6">
            <!-- Cover Image Card -->
            <div class="bg-white rounded-2xl border border-stone-200 p-6 shadow-sm">
              <label class="block font-bold text-stone-700 mb-4">封面展示</label>
              
              <div 
                class="relative aspect-[3/4] rounded-xl overflow-hidden bg-stone-100 border-2 border-dashed border-stone-300 group cursor-pointer hover:border-emerald-400 transition-colors"
                @click="$refs.fileInput.click()"
              >
                <img v-if="imagePreview" :src="imagePreview" class="w-full h-full object-cover" />
                <div v-else class="absolute inset-0 flex flex-col items-center justify-center text-stone-400">
                  <span class="text-4xl mb-2">📷</span>
                  <span class="text-sm font-medium">点击上传封面</span>
                </div>
                
                <!-- Hover Overlay -->
                <div class="absolute inset-0 bg-black/0 group-hover:bg-black/10 transition-colors flex items-center justify-center opacity-0 group-hover:opacity-100">
                  <span class="bg-white/90 px-4 py-2 rounded-full text-sm font-bold text-stone-700 shadow-sm">更换图片</span>
                </div>
              </div>
              <input ref="fileInput" type="file" @change="handleFileUpload" accept="image/*" class="hidden" />
              <p class="text-xs text-stone-400 mt-3 text-center">建议尺寸: 600x800 (竖版)</p>
            </div>

            <!-- Visibility Card -->
            <div class="bg-white rounded-2xl border border-stone-200 p-6 shadow-sm">
              <label class="block font-bold text-stone-700 mb-4">菜单可见性</label>
              <div class="flex items-center justify-between p-3 bg-stone-50 rounded-lg border border-stone-200 cursor-pointer" @click="form.is_public = !form.is_public">
                <div>
                  <div class="font-bold text-stone-800">公开显示</div>
                  <div class="text-xs text-stone-500">在顾客菜单中可见</div>
                </div>
                <div class="w-12 h-6 bg-stone-300 rounded-full relative transition-colors duration-300" :class="{ 'bg-emerald-500': form.is_public }">
                  <div class="w-5 h-5 bg-white rounded-full absolute top-0.5 left-0.5 transition-transform duration-300 shadow-sm" :class="{ 'translate-x-6': form.is_public }"></div>
                </div>
              </div>
            </div>
          </div>

          <!-- Right Column: Details -->
          <div class="lg:col-span-2 space-y-6">
            <!-- Basic Info Card -->
            <div class="bg-white rounded-2xl border border-stone-200 p-8 shadow-sm space-y-6">
              <h3 class="font-bold text-lg text-stone-800 border-b border-stone-100 pb-4 mb-6">基础信息</h3>
              
              <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div class="space-y-2">
                  <label class="text-sm font-bold text-stone-500 uppercase tracking-wider">菜品名称</label>
                  <input v-model="form.title" required class="w-full bg-stone-50 border border-stone-200 rounded-lg p-3 focus:ring-2 focus:ring-emerald-500 focus:bg-white focus:border-emerald-500 transition-all outline-none font-bold text-stone-800" placeholder="例如：红烧狮子头" />
                </div>
                <div class="space-y-2">
                  <label class="text-sm font-bold text-stone-500 uppercase tracking-wider">分类标签</label>
                  <input v-model="form.category" class="w-full bg-stone-50 border border-stone-200 rounded-lg p-3 focus:ring-2 focus:ring-emerald-500 focus:bg-white focus:border-emerald-500 transition-all outline-none" placeholder="例如：川菜 / 甜点" />
                </div>
              </div>

              <div class="space-y-2">
                <label class="text-sm font-bold text-stone-500 uppercase tracking-wider">对外介绍</label>
                <textarea v-model="form.description" rows="3" class="w-full bg-stone-50 border border-stone-200 rounded-lg p-3 focus:ring-2 focus:ring-emerald-500 focus:bg-white focus:border-emerald-500 transition-all outline-none leading-relaxed" placeholder="这道菜的特色是..."></textarea>
              </div>

              <div class="space-y-2">
                <label class="text-sm font-bold text-stone-500 uppercase tracking-wider">预计烹饪时长</label>
                <div class="relative">
                  <input v-model="form.cooking_time" type="number" class="w-full bg-stone-50 border border-stone-200 rounded-lg p-3 pl-10 focus:ring-2 focus:ring-emerald-500 focus:bg-white focus:border-emerald-500 transition-all outline-none font-mono" />
                  <span class="absolute left-3 top-3 text-stone-400">⏱️</span>
                  <span class="absolute right-3 top-3 text-stone-400 text-sm font-bold">分钟</span>
                </div>
              </div>
            </div>

            <!-- Chef Notes Card -->
            <div class="bg-amber-50 rounded-2xl border border-amber-100 p-8 shadow-inner relative overflow-hidden">
              <div class="absolute top-0 right-0 p-4 opacity-5 text-6xl pointer-events-none">📝</div>
              
              <div class="relative z-10">
                <label class="flex items-center gap-2 font-bold text-amber-900 mb-4">
                  <span>👨‍🍳</span> 主厨私密笔记
                  <span class="text-xs font-normal bg-amber-200/50 px-2 py-0.5 rounded text-amber-800">仅自己可见</span>
                </label>
                <textarea v-model="form.chef_notes" rows="6" class="w-full bg-white/50 border border-amber-200 rounded-lg p-4 focus:ring-2 focus:ring-amber-500 focus:bg-white focus:border-amber-500 transition-all outline-none text-stone-700 leading-relaxed placeholder-amber-900/30" placeholder="记录只有您知道的烹饪秘诀，比如：火候控制、特殊调料..."></textarea>
              </div>
            </div>
          </div>
        </div>

        <!-- 食材清单 Tab -->
        <div v-else-if="activeTab === 'ingredients'" key="ingredients">
          <div class="bg-white rounded-2xl border border-stone-200 p-6 shadow-sm">
            <div class="flex items-center justify-between mb-6">
              <div>
                <h3 class="font-bold text-lg text-stone-800">食材清单</h3>
                <p class="text-sm text-stone-500">列出制作这道菜需要的所有食材</p>
              </div>
              <button 
                @click="addIngredient"
                class="px-4 py-2 bg-emerald-500 text-white rounded-lg font-bold hover:bg-emerald-600 transition-colors flex items-center gap-2"
              >
                <span>+</span> 添加食材
              </button>
            </div>

            <!-- 空状态 -->
            <div v-if="ingredients.length === 0" class="text-center py-12 bg-stone-50 rounded-xl border-2 border-dashed border-stone-200">
              <span class="text-5xl mb-4 block">🥬</span>
              <p class="text-stone-500 mb-4">还没有添加食材</p>
              <button 
                @click="addIngredient"
                class="px-4 py-2 bg-emerald-500 text-white rounded-lg font-bold hover:bg-emerald-600 transition-colors"
              >
                添加第一个食材
              </button>
            </div>

            <!-- 食材列表 -->
            <div v-else class="space-y-3">
              <TransitionGroup name="list">
                <div 
                  v-for="(ing, index) in ingredients" 
                  :key="index"
                  class="flex items-center gap-4 p-4 bg-stone-50 rounded-xl border border-stone-200 group hover:bg-white hover:shadow-sm transition-all"
                >
                  <span class="w-8 h-8 bg-emerald-500 text-white rounded-full flex items-center justify-center font-bold text-sm flex-shrink-0">
                    {{ index + 1 }}
                  </span>
                  
                  <div class="flex-1 grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div class="relative">
                      <input 
                        v-model="ing.ingredient_name" 
                        class="w-full bg-white border border-stone-200 rounded-lg p-3 focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 transition-all outline-none"
                        placeholder="食材名称"
                        list="ingredient-suggestions"
                      />
                      <datalist id="ingredient-suggestions">
                        <option v-for="lib in ingredientLibrary" :key="lib.id" :value="lib.name" />
                      </datalist>
                    </div>
                    <input 
                      v-model="ing.quantity_display" 
                      class="w-full bg-white border border-stone-200 rounded-lg p-3 focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 transition-all outline-none"
                      placeholder="用量，如：200g、适量、2个"
                    />
                  </div>
                  
                  <button 
                    @click="removeIngredient(index)"
                    class="w-10 h-10 flex items-center justify-center text-stone-400 hover:text-red-500 hover:bg-red-50 rounded-lg transition-colors"
                    title="删除"
                  >
                    🗑️
                  </button>
                </div>
              </TransitionGroup>
            </div>

            <!-- 快速添加提示 -->
            <div v-if="ingredients.length > 0" class="mt-4 text-center">
              <button 
                @click="addIngredient"
                class="text-emerald-600 hover:text-emerald-700 font-medium text-sm"
              >
                + 继续添加食材
              </button>
            </div>
          </div>
        </div>

        <!-- 烹饪步骤 Tab -->
        <div v-else-if="activeTab === 'steps'" key="steps">
          <div class="bg-white rounded-2xl border border-stone-200 p-6 shadow-sm">
            <div class="flex items-center justify-between mb-6">
              <div>
                <h3 class="font-bold text-lg text-stone-800">烹饪步骤</h3>
                <p class="text-sm text-stone-500">按顺序描述烹饪过程，可以为每一步添加图片</p>
              </div>
              <button 
                @click="addStep"
                class="px-4 py-2 bg-emerald-500 text-white rounded-lg font-bold hover:bg-emerald-600 transition-colors flex items-center gap-2"
              >
                <span>+</span> 添加步骤
              </button>
            </div>

            <!-- 空状态 -->
            <div v-if="steps.length === 0" class="text-center py-12 bg-stone-50 rounded-xl border-2 border-dashed border-stone-200">
              <span class="text-5xl mb-4 block">👨‍🍳</span>
              <p class="text-stone-500 mb-4">还没有添加烹饪步骤</p>
              <button 
                @click="addStep"
                class="px-4 py-2 bg-emerald-500 text-white rounded-lg font-bold hover:bg-emerald-600 transition-colors"
              >
                添加第一个步骤
              </button>
            </div>

            <!-- 步骤列表 -->
            <div v-else class="space-y-4">
              <TransitionGroup name="list">
                <div 
                  v-for="(step, index) in steps" 
                  :key="index"
                  class="p-6 bg-stone-50 rounded-xl border border-stone-200 group hover:bg-white hover:shadow-sm transition-all"
                >
                  <div class="flex items-start gap-4">
                    <!-- 步骤编号和排序按钮 -->
                    <div class="flex flex-col items-center gap-1">
                      <button 
                        @click="moveStep(index, -1)"
                        :disabled="index === 0"
                        class="w-6 h-6 flex items-center justify-center text-stone-400 hover:text-stone-600 disabled:opacity-30 disabled:cursor-not-allowed"
                      >
                        ↑
                      </button>
                      <span class="w-10 h-10 bg-emerald-500 text-white rounded-full flex items-center justify-center font-bold">
                        {{ step.step_number }}
                      </span>
                      <button 
                        @click="moveStep(index, 1)"
                        :disabled="index === steps.length - 1"
                        class="w-6 h-6 flex items-center justify-center text-stone-400 hover:text-stone-600 disabled:opacity-30 disabled:cursor-not-allowed"
                      >
                        ↓
                      </button>
                    </div>
                    
                    <!-- 步骤内容 -->
                    <div class="flex-1 space-y-4">
                      <textarea 
                        v-model="step.description" 
                        rows="3"
                        class="w-full bg-white border border-stone-200 rounded-lg p-4 focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 transition-all outline-none resize-none"
                        :placeholder="`步骤 ${step.step_number} 的详细描述...`"
                      ></textarea>
                      
                      <!-- 步骤图片 -->
                      <div class="flex items-center gap-4">
                        <div 
                          class="relative w-24 h-24 rounded-lg overflow-hidden bg-stone-100 border-2 border-dashed border-stone-300 cursor-pointer hover:border-emerald-400 transition-colors flex-shrink-0"
                          @click="$refs[`stepImageInput${index}`][0].click()"
                        >
                          <img 
                            v-if="step.imagePreview" 
                            :src="step.imagePreview" 
                            class="w-full h-full object-cover"
                          />
                          <div v-else class="w-full h-full flex flex-col items-center justify-center text-stone-400">
                            <span class="text-xl">📷</span>
                            <span class="text-xs">添加图片</span>
                          </div>
                        </div>
                        <input 
                          :ref="`stepImageInput${index}`" 
                          type="file" 
                          @change="handleStepImageUpload($event, index)" 
                          accept="image/*" 
                          class="hidden" 
                        />
                        <p class="text-xs text-stone-400">可选：为这一步添加图片说明</p>
                      </div>
                    </div>
                    
                    <!-- 删除按钮 -->
                    <button 
                      @click="removeStep(index)"
                      class="w-10 h-10 flex items-center justify-center text-stone-400 hover:text-red-500 hover:bg-red-50 rounded-lg transition-colors"
                      title="删除步骤"
                    >
                      🗑️
                    </button>
                  </div>
                </div>
              </TransitionGroup>
            </div>

            <!-- 快速添加提示 -->
            <div v-if="steps.length > 0" class="mt-4 text-center">
              <button 
                @click="addStep"
                class="text-emerald-600 hover:text-emerald-700 font-medium text-sm"
              >
                + 继续添加步骤
              </button>
            </div>
          </div>
        </div>
      </Transition>

      <!-- 底部预览提示 -->
      <div class="mt-8 p-4 bg-blue-50 rounded-xl border border-blue-100 flex items-center gap-4">
        <span class="text-2xl">💡</span>
        <div class="flex-1">
          <p class="text-blue-800 font-medium">保存后可预览效果</p>
          <p class="text-blue-600 text-sm">保存菜谱后，可在菜单页面点击查看完整的翻书阅读效果</p>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
/* Tab 切换动画 */
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s ease;
}
.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

/* 列表动画 */
.list-enter-active,
.list-leave-active {
  transition: all 0.3s ease;
}
.list-enter-from,
.list-leave-to {
  opacity: 0;
  transform: translateX(-20px);
}
.list-move {
  transition: transform 0.3s ease;
}
</style>
