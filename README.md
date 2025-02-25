my_flask_app/
│
├── app/                          # Main application package
│   ├── __init__.py               # Initializes Flask app, loads config
│   ├── routes/                   # All route handlers (views)
│   │   ├── __init__.py
│   │   └── main_routes.py        # Main routes (e.g., index, get_data)
│   │
│   ├── models/                   # Data structures and logic (e.g., groups)
│   │   ├── __init__.py
│   │   └── group.py              # Group data structure and logic
│   │
│   ├── static/                   # Static files (CSS, JS, images)
│   │   └── css/
│   │       └── style.css
│   │
│   ├── templates/                # HTML templates (Jinja2)
│   │   └── index.html
│   │
│   └── utils/                    # Utility functions (logging, helpers)
│       ├── __init__.py
│       └── helpers.py
│
├── config/                       # Configuration files
│   ├── config_example.json       # Example config for groups/settings
│   ├── config.json               # Actual config (ignored by git)
│   └── settings.py               # Python config loader
│
├── instance/                     # Sensitive configs (e.g., secret keys)
│   └── config.py                 # Contains SECRET_KEY (ignored by git)
│
├── tests/                        # Unit and integration tests
│   └── test_app.py
│
├── .env                          # Environment variables (ignored by git)
├── .gitignore                    # Git ignore file
├── README.md                     # Project overview and setup
├── pyproject.toml                # Poetry dependency management
├── poetry.lock                   # Locked dependencies
└── run.py                        # Entry point to run the app
