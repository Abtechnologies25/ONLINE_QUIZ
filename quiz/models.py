from django.contrib.auth.models import User
from django.db import models


class QuizCategory(models.Model):
	name = models.CharField(max_length=120)
	day = models.PositiveIntegerField(help_text='Day number, for example 1 or 2.')
	description = models.TextField(blank=True)
	is_active = models.BooleanField(default=True)
	created_at = models.DateTimeField(auto_now_add=True)

	class Meta:
		ordering = ['id']
		verbose_name_plural = 'Quiz categories'

	def __str__(self):
		return f'Day {self.day}: {self.name}'


class Question(models.Model):
	category = models.ForeignKey(QuizCategory, on_delete=models.CASCADE, related_name='questions')
	text = models.TextField()
	option_a = models.CharField(max_length=255)
	option_b = models.CharField(max_length=255)
	option_c = models.CharField(max_length=255)
	option_d = models.CharField(max_length=255)
	correct_option = models.CharField(max_length=1, choices=[('A', 'A'), ('B', 'B'), ('C', 'C'), ('D', 'D')])

	def __str__(self):
		return self.text[:70]


class Attempt(models.Model):
	student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='attempts')
	category = models.ForeignKey(QuizCategory, on_delete=models.CASCADE, related_name='attempts')
	score = models.PositiveIntegerField(default=0)
	total_questions = models.PositiveIntegerField(default=0)
	started_at = models.DateTimeField(auto_now_add=True)
	finished_at = models.DateTimeField(auto_now=True)

	class Meta:
		ordering = ['-finished_at']
		constraints = [
			models.UniqueConstraint(fields=['student', 'category'], name='one_attempt_per_student_category')
		]

	@property
	def percentage(self):
		if not self.total_questions:
			return 0
		return round(self.score / self.total_questions * 100)

	def __str__(self):
		return f'{self.student.username} - {self.category} ({self.score}/{self.total_questions})'
