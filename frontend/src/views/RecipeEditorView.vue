<script setup>
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import axios from 'axios'
import API_BASE_URL from '../config/api'

const route = useRoute()
const router = useRouter()
const isEdit = route.params.id !== undefined

const form = ref({
    title: '',
    description: '',
    cooking_time: 30,
    category: '',
    is_public: true,
    chef_notes: '',
    cover_image: null 
})

const imagePreview = ref(null)
const loading = ref(false)

onMounted(async () => {
    if (isEdit) {
        loading.value = true
        try {
            const { data } = await axios.get(`${API_BASE_URL}/api/recipes/${route.params.id}/?mode=chef`)
            form.value = { ...data, cover_image: null } 
            imagePreview.value = data.cover_image
        } catch (e) {
            alert('加载失败')
        } finally {
            loading.value = false
        }
    }
})

const handleFileUpload = (event) => {
    const file = event.target.files[0]
    if (file) {
        form.value.cover_image = file
        imagePreview.value = URL.createObjectURL(file)
    }
}

const submit = async () => {
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

    try {
        if (isEdit) {
            await axios.patch(`${API_BASE_URL}/api/recipes/${route.params.id}/`, formData)
        } else {
            await axios.post(`${API_BASE_URL}/api/recipes/`, formData)
        }
        router.push('/chef/recipes')
    } catch (e) {
        console.error(e)
        alert('保存失败: ' + (e.response?.data?.detail || e.message))
    }
}
</script>

<template>
  <div class="max-w-6xl mx-auto py-8 px-4">
    <!-- Header -->
    <div class="flex items-center justify-between mb-8">
        <div class="flex items-center gap-4">
            <router-link to="/chef/recipes" class="w-10 h-10 flex items-center justify-center rounded-full bg-white border border-stone-200 text-stone-500 hover:bg-stone-50 transition-colors">
                ←
            </router-link>
            <div>
                <h1 class="text-2xl font-bold text-stone-800 font-display">{{ isEdit ? '编辑菜谱' : '新增菜谱' }}</h1>
                <p class="text-sm text-stone-500">完善您的美味杰作</p>
            </div>
        </div>
        <div class="flex gap-3">
             <button @click="router.push('/chef/recipes')" class="px-4 py-2 rounded-lg text-stone-600 font-bold hover:bg-stone-100 transition-colors">
                取消
             </button>
             <button @click="submit" class="px-6 py-2 rounded-lg bg-emerald-600 text-white font-bold hover:bg-emerald-700 shadow-lg shadow-emerald-200 transition-all hover:-translate-y-0.5 flex items-center gap-2">
                <span>💾</span> 保存更改
             </button>
        </div>
    </div>

    <div class="grid grid-cols-1 lg:grid-cols-3 gap-8">
        
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
            
            <!-- Helper Link -->
            <div class="text-right">
                <a href="/admin" target="_blank" class="inline-flex items-center gap-1 text-sm text-stone-400 hover:text-emerald-600 transition-colors">
                    需要编辑步骤详情？前往高级后台 ↗
                </a>
            </div>
        </div>
    </div>
  </div>
</template>
