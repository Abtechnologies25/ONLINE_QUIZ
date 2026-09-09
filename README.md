# Quiz

A Django quiz platform with separate staff and student dashboards.

## Features

- Superuser/staff login for the admin dashboard
- Admin-created student usernames and passwords
- Day-wise quiz categories
- Multiple-choice questions and one-attempt-per-student protection
- Automatic score and percentage calculation after submission
- Admin result table showing every student's marks
- Django admin for adding more questions and managing records

## Run locally

```powershell
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

Open `http://127.0.0.1:8000/`. Sign in with the superuser credentials. Use **Add student** to create learner credentials and **Create quiz** to publish the first question for a day. Additional questions can be added from `http://127.0.0.1:8000/admin/`.
