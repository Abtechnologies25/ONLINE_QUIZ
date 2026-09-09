from django.contrib.auth.models import User
from django.test import TestCase

from .models import Attempt, Question, QuizCategory


class QuizManagementTests(TestCase):
	def setUp(self):
		self.admin = User.objects.create_user(username='admin', password='password', is_staff=True)
		self.client.force_login(self.admin)
		self.category = QuizCategory.objects.create(name='Python basics', day=1)

	def question_data(self, text='What is Python?'):
		return {
			'day': self.category.day,
			'category_id': self.category.id,
			'question_text': text,
			'option_a': 'A',
			'option_b': 'B',
			'option_c': 'C',
			'option_d': 'D',
			'correct_option': 'A',
		}

	def test_can_add_multiple_questions_to_one_category(self):
		self.client.post('/quizzes/add/', self.question_data())
		self.client.post('/quizzes/add/', self.question_data('What is Django?'))

		self.assertEqual(self.category.questions.count(), 2)

	def test_can_add_multiple_questions_in_one_submission(self):
		data = {
			'day': self.category.day,
			'category_id': self.category.id,
			'question_text': ['What is Python?', 'What is Django?'],
			'option_a': ['A1', 'A2'],
			'option_b': ['B1', 'B2'],
			'option_c': ['C1', 'C2'],
			'option_d': ['D1', 'D2'],
			'correct_option': ['A', 'B'],
		}

		response = self.client.post('/quizzes/add/', data)

		self.assertRedirects(response, '/quizzes/add/')
		self.assertEqual(self.category.questions.count(), 2)
		self.assertEqual(list(self.category.questions.values_list('text', flat=True)), ['What is Python?', 'What is Django?'])

	def test_can_edit_and_delete_question(self):
		question = Question.objects.create(category=self.category, text='Old question', option_a='A', option_b='B', option_c='C', option_d='D', correct_option='A')

		response = self.client.post(f'/questions/{question.id}/edit/', self.question_data('Updated question'))
		self.assertRedirects(response, '/')
		question.refresh_from_db()
		self.assertEqual(question.text, 'Updated question')

		response = self.client.post(f'/questions/{question.id}/delete/')
		self.assertRedirects(response, '/')
		self.assertFalse(Question.objects.filter(id=question.id).exists())

	def test_management_pages_render(self):
		question = Question.objects.create(category=self.category, text='Question', option_a='A', option_b='B', option_c='C', option_d='D', correct_option='A')

		self.assertEqual(self.client.get('/categories/add/').status_code, 200)
		self.assertEqual(self.client.get('/quizzes/add/').status_code, 200)
		self.assertEqual(self.client.get(f'/questions/{question.id}/edit/').status_code, 200)

	def test_question_must_belong_to_selected_day(self):
		response = self.client.post('/quizzes/add/', {**self.question_data(), 'day': 99})

		self.assertEqual(response.status_code, 404)
		self.assertEqual(self.category.questions.count(), 0)

class CategoryManagementTests(TestCase):
	def test_staff_can_create_category(self):
		admin = User.objects.create_user(username='admin', password='password', is_staff=True)
		self.client.force_login(admin)

		response = self.client.post('/categories/add/', {'name': 'Django', 'day': 2, 'description': 'Web basics'})

		self.assertRedirects(response, '/quizzes/add/')
		self.assertTrue(QuizCategory.objects.filter(name='Django', day=2).exists())

	def test_staff_can_edit_category(self):
		admin = User.objects.create_user(username='admin', password='password', is_staff=True)
		category = QuizCategory.objects.create(name='Python', day=1)
		self.client.force_login(admin)

		response = self.client.post(f'/categories/{category.id}/edit/', {'name': 'Advanced Python', 'day': 2, 'description': 'Updated'})

		self.assertRedirects(response, '/days/2/')
		category.refresh_from_db()
		self.assertEqual(category.name, 'Advanced Python')
		self.assertEqual(category.day, 2)

	def test_staff_can_delete_category_and_questions(self):
		admin = User.objects.create_user(username='admin', password='password', is_staff=True)
		category = QuizCategory.objects.create(name='Python', day=1)
		question = Question.objects.create(category=category, text='Question', option_a='A', option_b='B', option_c='C', option_d='D', correct_option='A')
		self.client.force_login(admin)

		response = self.client.post(f'/categories/{category.id}/delete/')

		self.assertRedirects(response, '/')
		self.assertFalse(QuizCategory.objects.filter(id=category.id).exists())
		self.assertFalse(Question.objects.filter(id=question.id).exists())


class StudentDashboardTests(TestCase):
	def test_categories_from_same_day_are_shown_under_one_day(self):
		student = User.objects.create_user(username='student', password='password')
		self.client.force_login(student)
		QuizCategory.objects.create(name='Python', day=1)
		QuizCategory.objects.create(name='Django', day=1)
		QuizCategory.objects.create(name='SQL', day=2)

		response = self.client.get('/')

		self.assertEqual(response.status_code, 200)
		content = response.content.decode()
		self.assertEqual(content.count('DAY 01'), 1)
		self.assertIn('Python', content)
		self.assertIn('Django', content)
		self.assertIn('DAY 02', content)

	def test_student_sees_one_percentage_for_a_day(self):
		student = User.objects.create_user(username='student', password='password')
		first_category = QuizCategory.objects.create(name='Python', day=1)
		second_category = QuizCategory.objects.create(name='Django', day=1)
		Attempt.objects.create(student=student, category=first_category, score=2, total_questions=2)
		Attempt.objects.create(student=student, category=second_category, score=1, total_questions=2)
		self.client.force_login(student)

		response = self.client.get('/')

		self.assertContains(response, 'Day percentage')
		self.assertContains(response, '75%')


class AdminDashboardTests(TestCase):
	def test_day_button_opens_questions_page(self):
		admin = User.objects.create_user(username='admin', password='password', is_staff=True)
		category = QuizCategory.objects.create(name='Python', day=1)
		Question.objects.create(category=category, text='What is Python?', option_a='A', option_b='B', option_c='C', option_d='D', correct_option='A')
		self.client.force_login(admin)

		response = self.client.get('/days/1/')

		self.assertEqual(response.status_code, 200)
		self.assertContains(response, 'Python')
		self.assertContains(response, 'What is Python?')

	def test_admin_library_groups_categories_under_one_day(self):
		admin = User.objects.create_user(username='admin', password='password', is_staff=True)
		QuizCategory.objects.create(name='Python', day=1)
		QuizCategory.objects.create(name='Django', day=1)
		student = User.objects.create_user(username='student', password='password')
		self.client.force_login(admin)

		response = self.client.get('/')
		content = response.content.decode()

		self.assertContains(response, 'Student list')
		self.assertContains(response, 'student')
		self.assertContains(response, f'/students/{student.id}/')
		self.assertContains(response, 'Quiz library by day')
		self.assertEqual(content.count('DAY 01'), 1)
		self.assertIn('/days/1/', content)

	def test_admin_sees_one_percentage_for_a_student_day(self):
		admin = User.objects.create_user(username='admin', password='password', is_staff=True)
		student = User.objects.create_user(username='student', password='password')
		first_category = QuizCategory.objects.create(name='Python', day=1)
		second_category = QuizCategory.objects.create(name='Django', day=1)
		Attempt.objects.create(student=student, category=first_category, score=3, total_questions=4)
		Attempt.objects.create(student=student, category=second_category, score=2, total_questions=4)
		self.client.force_login(admin)

		response = self.client.get('/')

		self.assertContains(response, 'Student list')
		self.assertContains(response, f'/students/{student.id}/')

	def test_admin_can_view_student_quiz_details(self):
		admin = User.objects.create_user(username='admin', password='password', is_staff=True)
		student = User.objects.create_user(username='student', password='password')
		category = QuizCategory.objects.create(name='Python', day=1)
		Attempt.objects.create(student=student, category=category, score=3, total_questions=4)
		self.client.force_login(admin)

		response = self.client.get(f'/students/{student.id}/')

		self.assertEqual(response.status_code, 200)
		self.assertContains(response, 'student')
		self.assertContains(response, 'Python')
		self.assertContains(response, '3/4')
		self.assertContains(response, '75%')

	def test_staff_can_edit_day_for_all_categories(self):
		admin = User.objects.create_user(username='admin', password='password', is_staff=True)
		first_category = QuizCategory.objects.create(name='Python', day=1)
		second_category = QuizCategory.objects.create(name='Django', day=1)
		self.client.force_login(admin)

		response = self.client.post('/days/1/edit/', {'day': 2})

		self.assertRedirects(response, '/days/2/')
		self.assertEqual(set(QuizCategory.objects.values_list('day', flat=True)), {2})
		self.assertEqual(first_category.name, QuizCategory.objects.get(name='Python').name)
		self.assertEqual(second_category.name, QuizCategory.objects.get(name='Django').name)

	def test_staff_can_delete_day_and_all_categories(self):
		admin = User.objects.create_user(username='admin', password='password', is_staff=True)
		category = QuizCategory.objects.create(name='Python', day=1)
		Question.objects.create(category=category, text='Question', option_a='A', option_b='B', option_c='C', option_d='D', correct_option='A')
		self.client.force_login(admin)

		response = self.client.post('/days/1/delete/')

		self.assertRedirects(response, '/')
		self.assertFalse(QuizCategory.objects.filter(day=1).exists())
		self.assertFalse(Question.objects.exists())
