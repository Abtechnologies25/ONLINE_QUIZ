from collections import defaultdict

from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.models import User
from django.db import IntegrityError
from django.shortcuts import get_object_or_404, redirect, render

from .models import Attempt, Question, QuizCategory


def login_view(request):
	if request.user.is_authenticated:
		return redirect('dashboard')
	form = AuthenticationForm(request, data=request.POST or None)
	if request.method == 'POST' and form.is_valid():
		login(request, form.get_user())
		return redirect('dashboard')
	return render(request, 'quiz/login.html', {'form': form})


def staff_only(user):
	return user.is_authenticated and user.is_staff


def build_day_result(attempts):
	result = defaultdict(lambda: {'score': 0, 'total_questions': 0})
	for attempt in attempts:
		day_result = result[attempt.category.day]
		day_result['score'] += attempt.score
		day_result['total_questions'] += attempt.total_questions
	for day_result in result.values():
		total_questions = day_result['total_questions']
		day_result['percentage'] = round(day_result['score'] / total_questions * 100) if total_questions else 0
	return dict(result)


@login_required
def dashboard(request):
	if request.user.is_staff:
		students = User.objects.filter(is_staff=False).order_by('username')
		attempts = list(Attempt.objects.select_related('student', 'category').order_by('student__username', 'category__day'))
		day_results = defaultdict(lambda: {'score': 0, 'total_questions': 0})
		for attempt in attempts:
			key = (attempt.student_id, attempt.category.day)
			day_result = day_results[key]
			day_result['student'] = attempt.student
			day_result['day'] = attempt.category.day
			day_result['score'] += attempt.score
			day_result['total_questions'] += attempt.total_questions
		for day_result in day_results.values():
			total_questions = day_result['total_questions']
			day_result['percentage'] = round(day_result['score'] / total_questions * 100) if total_questions else 0
		return render(request, 'quiz/admin_dashboard.html', {'students': students, 'attempts': attempts, 'day_results': day_results.values(), 'categories': QuizCategory.objects.all()})
	categories = QuizCategory.objects.filter(is_active=True).prefetch_related('questions')
	student_attempts = list(Attempt.objects.filter(student=request.user).select_related('category'))
	attempts = {attempt.category_id: attempt for attempt in student_attempts}
	return render(request, 'quiz/student_dashboard.html', {'categories': categories, 'attempts': attempts, 'day_results': build_day_result(student_attempts)})


@login_required
@user_passes_test(staff_only)
def day_questions(request, day):
	categories = QuizCategory.objects.filter(day=day).prefetch_related('questions')
	if not categories.exists():
		return redirect('dashboard')
	return render(request, 'quiz/day_questions.html', {'day': day, 'categories': categories})


@login_required
@user_passes_test(staff_only)
def add_student(request):
	if request.method == 'POST':
		username = request.POST.get('username', '').strip()
		password = request.POST.get('password', '')
		if not username or not password:
			messages.error(request, 'Username and password are required.')
		elif User.objects.filter(username=username).exists():
			messages.error(request, 'That username already exists.')
		else:
			User.objects.create_user(username=username, password=password)
			messages.success(request, f'Student {username} created successfully.')
			return redirect('dashboard')
	return render(request, 'quiz/add_student.html')


@login_required
@user_passes_test(staff_only)
def add_category(request):
	if request.method == 'POST':
		name = request.POST.get('name', '').strip()
		day = request.POST.get('day', '').strip()
		description = request.POST.get('description', '').strip()
		if not name or not day:
			messages.error(request, 'Category name and day are required.')
		else:
			try:
				QuizCategory.objects.create(name=name, day=int(day), description=description)
			except (ValueError, IntegrityError):
				messages.error(request, 'Please enter a valid day.')
			else:
				messages.success(request, 'Category created successfully. Add questions to it now.')
				return redirect('add_quiz')
	return render(request, 'quiz/add_category.html')


@login_required
@user_passes_test(staff_only)
def add_quiz(request):
	categories = QuizCategory.objects.all()
	days = QuizCategory.objects.values_list('day', flat=True).distinct().order_by('day')
	if request.method == 'POST':
		day = request.POST.get('day', '').strip()
		category_id = request.POST.get('category_id', '').strip()
		question_text = request.POST.get('question_text', '').strip()
		if not day or not category_id or not question_text:
			messages.error(request, 'Choose a day, category, and enter a question.')
		else:
			try:
				category = get_object_or_404(QuizCategory, id=category_id, day=int(day))
				Question.objects.create(
					category=category, text=question_text,
					option_a=request.POST.get('option_a', ''), option_b=request.POST.get('option_b', ''),
					option_c=request.POST.get('option_c', ''), option_d=request.POST.get('option_d', ''),
					correct_option=request.POST.get('correct_option', 'A'),
				)
			except (ValueError, IntegrityError):
				messages.error(request, 'Please enter a valid day and question details.')
			else:
				messages.success(request, 'Question added to the category.')
				return redirect('add_quiz')
	return render(request, 'quiz/add_quiz.html', {'categories': categories, 'days': days})


@login_required
@user_passes_test(staff_only)
def edit_question(request, question_id):
	question = get_object_or_404(Question, id=question_id)
	if request.method == 'POST':
		question.category_id = request.POST.get('category_id')
		question.text = request.POST.get('question_text', '').strip()
		question.option_a = request.POST.get('option_a', '').strip()
		question.option_b = request.POST.get('option_b', '').strip()
		question.option_c = request.POST.get('option_c', '').strip()
		question.option_d = request.POST.get('option_d', '').strip()
		question.correct_option = request.POST.get('correct_option', 'A')
		if not question.category_id or not all([question.text, question.option_a, question.option_b, question.option_c, question.option_d]):
			messages.error(request, 'All question fields are required.')
		else:
			question.save()
			messages.success(request, 'Question updated successfully.')
			return redirect('dashboard')
	return render(request, 'quiz/edit_question.html', {'question': question, 'categories': QuizCategory.objects.all()})


@login_required
@user_passes_test(staff_only)
def delete_question(request, question_id):
	question = get_object_or_404(Question, id=question_id)
	if request.method == 'POST':
		question.delete()
		messages.success(request, 'Question deleted successfully.')
	return redirect('dashboard')


@login_required
def take_quiz(request, category_id):
	if request.user.is_staff:
		return redirect('dashboard')
	category = get_object_or_404(QuizCategory, id=category_id, is_active=True)
	questions = list(category.questions.all())
	if not questions:
		messages.info(request, 'This quiz has no questions yet.')
		return redirect('dashboard')
	if Attempt.objects.filter(student=request.user, category=category).exists():
		messages.info(request, 'You have already completed this quiz.')
		return redirect('dashboard')
	if request.method == 'POST':
		score = sum(request.POST.get(f'question_{question.id}') == question.correct_option for question in questions)
		Attempt.objects.create(student=request.user, category=category, score=score, total_questions=len(questions))
		return render(request, 'quiz/result.html', {'category': category, 'score': score, 'total': len(questions), 'percentage': round(score / len(questions) * 100)})
	return render(request, 'quiz/take_quiz.html', {'category': category, 'questions': questions})
