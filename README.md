# Programming Help Forum

A comprehensive Flask-based web application for a programming help forum.

## Features

- User registration and login with hashed passwords
- Post questions categorized by programming topics
- Filter questions by selected topics
- Answer questions
- Upvote and downvote answers
- Responsive design with Bootstrap

## Local Development

1. Clone or download the repository.
2. Create a virtual environment: `python -m venv .venv`
3. Activate the environment: `.venv\Scripts\activate` (Windows)
4. Install dependencies: `pip install -r requirements.txt`
5. Run the application: `python app.py`
6. Open http://127.0.0.1:5000 in your browser.

## Hosting on PythonAnywhere

1. Create a PythonAnywhere account.
2. Upload the project files to your PythonAnywhere directory.
3. Set up a MySQL database in PythonAnywhere.
4. Update `config.py` to use the MySQL database URL:
   ```python
   SQLALCHEMY_DATABASE_URI = 'mysql://username:password@host/dbname'
   ```
5. In the Web tab, set the WSGI configuration file to `wsgi.py`.
6. Reload the web app.

## Technologies Used

- Flask
- SQLAlchemy
- Flask-Login
- Flask-WTF
- Bootstrap 5
- Werkzeug (for password hashing)