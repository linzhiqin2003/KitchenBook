from django.contrib import admin
from django.utils.html import format_html
from django.db.models import Count
from .models import Question


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    """
    Question 模型的后台管理配置
    支持：列表展示、搜索、过滤、批量操作、详细编辑
    """
    
    # ========== 列表页配置 ==========
    list_display = [
        'id',
        'course_id',
        'topic_display',
        'difficulty_badge',
        'question_preview',
        'options_count',
        'created_at',
    ]
    
    list_display_links = ['id', 'question_preview']
    
    list_filter = [
        'course_id',
        'difficulty',
        'topic',
        'created_at',
    ]
    
    search_fields = [
        'question_text',
        'options',
        'answer',
        'explanation',
        'topic',
    ]
    
    ordering = ['-created_at']
    
    list_per_page = 25
    
    date_hierarchy = 'created_at'
    
    # ========== 详情页配置 ==========
    fieldsets = [
        ('基本信息', {
            'fields': ['course_id', 'topic', 'difficulty']
        }),
        ('题目内容', {
            'fields': ['question_text', 'options', 'answer'],
            'classes': ['wide']
        }),
        ('解释说明', {
            'fields': ['explanation', 'seed_question', 'source_files'],
            'classes': ['wide', 'collapse']  # 默认折叠
        }),
        ('元数据', {
            'fields': ['created_at'],
            'classes': ['collapse']
        }),
    ]
    
    readonly_fields = ['created_at']
    
    # ========== 批量操作 ==========
    actions = ['set_easy', 'set_medium', 'set_hard', 'duplicate_questions']
    
    @admin.action(description='设为 Easy 难度')
    def set_easy(self, request, queryset):
        count = queryset.update(difficulty='easy')
        self.message_user(request, f'已将 {count} 道题目设为 Easy 难度')
    
    @admin.action(description='设为 Medium 难度')
    def set_medium(self, request, queryset):
        count = queryset.update(difficulty='medium')
        self.message_user(request, f'已将 {count} 道题目设为 Medium 难度')
    
    @admin.action(description='设为 Hard 难度')
    def set_hard(self, request, queryset):
        count = queryset.update(difficulty='hard')
        self.message_user(request, f'已将 {count} 道题目设为 Hard 难度')
    
    @admin.action(description='复制选中的题目')
    def duplicate_questions(self, request, queryset):
        count = 0
        for q in queryset:
            q.pk = None  # 清除主键，保存时会创建新记录
            q.save()
            count += 1
        self.message_user(request, f'已复制 {count} 道题目')
    
    # ========== 自定义显示方法 ==========
    @admin.display(description='主题')
    def topic_display(self, obj):
        """格式化显示主题名称"""
        topic = obj.topic or ''
        # 移除数字前缀，如 "07-debugging" -> "debugging"
        parts = topic.split('-')
        if len(parts) > 1 and parts[0].isdigit():
            topic = '-'.join(parts[1:])
        return topic.title().replace('-', ' ')
    
    @admin.display(description='难度')
    def difficulty_badge(self, obj):
        """用颜色标签显示难度"""
        colors = {
            'easy': '#28a745',    # 绿色
            'medium': '#ffc107',  # 黄色
            'hard': '#dc3545',    # 红色
        }
        labels = {
            'easy': '🟢 Easy',
            'medium': '🟡 Medium',
            'hard': '🔴 Hard',
        }
        color = colors.get(obj.difficulty, '#6c757d')
        label = labels.get(obj.difficulty, obj.difficulty)
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color, label
        )
    
    @admin.display(description='题目预览')
    def question_preview(self, obj):
        """显示题目文本的前 80 个字符"""
        text = obj.question_text or ''
        if len(text) > 80:
            return text[:80] + '...'
        return text
    
    @admin.display(description='选项数')
    def options_count(self, obj):
        """显示选项数量"""
        if obj.options and isinstance(obj.options, list):
            return len(obj.options)
        return 0
    
    # ========== 优化性能 ==========
    def get_queryset(self, request):
        """优化查询性能"""
        return super().get_queryset(request).defer('explanation', 'seed_question')


# 自定义 Admin 站点标题
admin.site.site_header = 'KitchenBook 后台管理'
admin.site.site_title = 'KitchenBook Admin'
admin.site.index_title = '欢迎使用 KitchenBook 管理后台'
