from django.contrib import admin

from .models import Attempt, Question, QuizCategory


@admin.register(QuizCategory)
class QuizCategoryAdmin(admin.ModelAdmin):
	list_display = ('name', 'day', 'is_active', 'created_at')
	list_filter = ('is_active', 'day')
	search_fields = ('name',)


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
	list_display = ('text', 'category', 'correct_option')
	list_filter = ('category',)


@admin.register(Attempt)
class AttemptAdmin(admin.ModelAdmin):
	list_display = ('student', 'category', 'score', 'total_questions', 'percentage', 'finished_at')
	list_filter = ('category',)
	search_fields = ('student__username',)
	readonly_fields = ('finished_at',)
from django.contrib import admin

# Register your models here.
