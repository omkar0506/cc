"""
Seed data script for AI-Powered Adaptive Interviewer & Evaluation System.
Populates normalized skills with aliases, job roles, role-skill mappings,
approved question bank (at least 8 approved questions per seeded skill), and default application settings.
"""

from app.extensions import db
from app.models.job import JobRole, Skill, JobRoleSkill
from app.models.question import Question
from app.models.admin import AppSetting


def seed_all():
    print("Seeding initial application data...")

    # 1. Default App Settings
    settings_data = [
        (
            'scoring_weights_technical',
            {
                'correctness': 0.35,
                'problem_solving': 0.25,
                'relevance_completeness': 0.20,
                'explanation_clarity': 0.10,
                'code_quality': 0.10
            },
            'Rubric weights for technical interviews'
        ),
        (
            'scoring_weights_hr',
            {
                'relevance': 0.30,
                'specificity': 0.25,
                'structure': 0.20,
                'actions_and_outcomes': 0.25
            },
            'Rubric weights for HR and situational interviews'
        ),
        (
            'adaptive_policy',
            {
                'high_threshold': 0.80,
                'low_threshold': 0.40,
                'max_followups_per_skill': 2,
                'max_followups_per_question': 1,
                'max_session_questions': 10,
                'min_session_questions': 3
            },
            'Adaptive state machine thresholds and caps'
        ),
        (
            'evidence_thresholds',
            {
                'demonstrated_min_answers': 2,
                'demonstrated_min_ratio': 0.70,
                'demonstrated_requires_medium_hard': True,
                'partial_min_ratio': 0.40,
                'partial_max_ratio': 0.69
            },
            'Skill evidence classification boundaries'
        ),
        (
            'gap_priority_factors',
            {
                'Demonstrated': 0.0,
                'Partially demonstrated': 0.5,
                'Needs further assessment': 0.75,
                'Not yet assessed': 1.0
            },
            'Priority formula factors: priority_score = importance_weight * gap_factor'
        )
    ]

    for key, val, desc in settings_data:
        AppSetting.set_setting(key, val, desc)
    print("Application settings initialized.")

    # 2. Skills with Aliases
    skills_data = [
        {
            'name': 'Python',
            'slug': 'python',
            'category': 'technical',
            'description': 'Python programming language, syntax, data structures, and memory model.',
            'aliases': ['Python', 'Python 3', 'Python3', 'Py', 'CPython']
        },
        {
            'name': 'Object-Oriented Programming (OOP)',
            'slug': 'oop',
            'category': 'technical',
            'description': 'Object-oriented programming concepts: encapsulation, inheritance, polymorphism, abstraction.',
            'aliases': ['OOP', 'Object-Oriented Programming', 'Object Oriented Design', 'OOD', 'OOPs']
        },
        {
            'name': 'Flask',
            'slug': 'flask',
            'category': 'technical',
            'description': 'Lightweight Python web framework, WSGI, routing, templates, and application factory.',
            'aliases': ['Flask', 'Flask Web Framework', 'Flask-RESTful', 'Werkzeug']
        },
        {
            'name': 'SQL & Relational Databases',
            'slug': 'sql',
            'category': 'technical',
            'description': 'Relational database schema design, querying, joins, indexing, normalization, and ACID transactions.',
            'aliases': ['SQL', 'MySQL', 'PostgreSQL', 'Relational Databases', 'RDBMS', 'SQLite']
        },
        {
            'name': 'Java',
            'slug': 'java',
            'category': 'technical',
            'description': 'Core Java, JVM architecture, memory management, multithreading, and collections framework.',
            'aliases': ['Java', 'Core Java', 'Java 8', 'Java 17', 'Java 21', 'Java SE', 'JVM']
        },
        {
            'name': 'Spring Boot',
            'slug': 'spring-boot',
            'category': 'technical',
            'description': 'Spring Boot ecosystem, dependency injection, annotations, REST controllers, and Spring Data.',
            'aliases': ['Spring Boot', 'Spring', 'Spring Framework', 'Spring MVC', 'Spring Data']
        },
        {
            'name': 'Data Analysis & Pandas',
            'slug': 'data-analysis',
            'category': 'technical',
            'description': 'Data wrangling, aggregation, filtering, exploratory analysis using Pandas and NumPy.',
            'aliases': ['Pandas', 'Data Analysis', 'NumPy', 'Data Wrangling', 'EDA']
        },
        {
            'name': 'Behavioral & Situational Communication',
            'slug': 'behavioral-communication',
            'category': 'hr',
            'description': 'STAR-method communication, conflict resolution, teamwork, ownership, and adaptability.',
            'aliases': ['Communication', 'Teamwork', 'Behavioral', 'Situational', 'Conflict Resolution', 'Collaboration']
        }
    ]

    skill_records = {}
    for s_item in skills_data:
        existing = Skill.query.filter_by(slug=s_item['slug']).first()
        if not existing:
            existing = Skill(**s_item)
            db.session.add(existing)
            db.session.flush()
        skill_records[s_item['slug']] = existing
    print(f"Skills seeded: {len(skill_records)} skills.")

    # 3. Job Roles
    roles_data = [
        {
            'title': 'Python Developer',
            'slug': 'python-developer',
            'description': 'Responsible for developing robust backend services, APIs, data manipulation pipelines, and integrating databases using modern Python.',
            'experience_level': 'Entry to Mid-Level',
            'interview_topics': ['Python Core & Internals', 'OOP Design', 'Flask Framework', 'SQL & Databases', 'STAR Behavioral'],
            'difficulty_distribution': {'easy': 30, 'medium': 50, 'hard': 20},
            'skills': [
                ('python', 3.0, True),
                ('oop', 2.5, True),
                ('flask', 2.0, False),
                ('sql', 2.5, True),
                ('behavioral-communication', 1.5, False)
            ]
        },
        {
            'title': 'Java Developer',
            'slug': 'java-developer',
            'description': 'Engineers enterprise backend applications, RESTful microservices, and high-performance transactional services with Java and Spring Boot.',
            'experience_level': 'Entry to Mid-Level',
            'interview_topics': ['Core Java & Collections', 'OOP Principles', 'Spring Boot & Dependency Injection', 'SQL & JPA', 'STAR Behavioral'],
            'difficulty_distribution': {'easy': 30, 'medium': 50, 'hard': 20},
            'skills': [
                ('java', 3.0, True),
                ('oop', 2.5, True),
                ('spring-boot', 2.5, True),
                ('sql', 2.0, True),
                ('behavioral-communication', 1.5, False)
            ]
        },
        {
            'title': 'Data Analyst',
            'slug': 'data-analyst',
            'description': 'Analyzes complex datasets, designs relational SQL queries, generates actionable business insights, and cleans data using Python and Pandas.',
            'experience_level': 'Entry to Mid-Level',
            'interview_topics': ['SQL Querying & Joins', 'Pandas & Data Wrangling', 'Python Basics', 'Statistical Reasoning', 'STAR Behavioral'],
            'difficulty_distribution': {'easy': 40, 'medium': 45, 'hard': 15},
            'skills': [
                ('sql', 3.0, True),
                ('data-analysis', 3.0, True),
                ('python', 2.0, True),
                ('behavioral-communication', 1.5, False)
            ]
        }
    ]

    role_records = {}
    for r_item in roles_data:
        existing_role = JobRole.query.filter_by(slug=r_item['slug']).first()
        if not existing_role:
            skills_cfg = r_item.pop('skills')
            existing_role = JobRole(**r_item)
            db.session.add(existing_role)
            db.session.flush()

            for skill_slug, weight, is_req in skills_cfg:
                jrs = JobRoleSkill(
                    job_role_id=existing_role.id,
                    skill_id=skill_records[skill_slug].id,
                    importance_weight=weight,
                    is_required=is_req
                )
                db.session.add(jrs)
        role_records[r_item['slug']] = existing_role
    print(f"Job roles seeded: {len(role_records)} roles.")

    # 4. Question Bank (8+ approved questions per seeded skill)
    # We will define a structured catalog of sample questions for each skill
    questions_catalog = [
        # Skill: Python (8 questions)
        {
            'role_slug': 'python-developer',
            'skill_slug': 'python',
            'question_type': 'technical',
            'difficulty': 'easy',
            'question_text': 'Explain the difference between mutable and immutable data types in Python. Give two examples of each.',
            'expected_concepts': ['mutable can be changed in place', 'immutable cannot be modified after creation', 'list/dict/set as mutable', 'int/str/tuple as immutable', 'id or memory address'],
            'reference_answer': 'In Python, mutable objects can be modified after creation without changing their identity (memory address), such as lists, dictionaries, and sets. Immutable objects cannot be altered once instantiated; any modification creates a new object in memory. Examples of immutable types include integers, strings, tuples, and frozensets.',
            'rubric': {'correctness': 0.40, 'completeness': 0.30, 'clarity': 0.30}
        },
        {
            'role_slug': 'python-developer',
            'skill_slug': 'python',
            'question_type': 'technical',
            'difficulty': 'easy',
            'question_text': 'What are Python list comprehensions, and how do they differ from using a traditional for-loop with append()?',
            'expected_concepts': ['concise syntax', 'creates a new list in a single expression', 'readability', 'optimized in CPython bytecode'],
            'reference_answer': 'A list comprehension provides a concise and expressive syntax for creating a new list based on an existing iterable, combining iteration, optional filtering, and mapping in one line. Compared to a manual for-loop with append(), comprehensions are generally faster because the bytecode avoids method lookup overhead.',
            'rubric': {'correctness': 0.40, 'completeness': 0.30, 'clarity': 0.30}
        },
        {
            'role_slug': 'python-developer',
            'skill_slug': 'python',
            'question_type': 'technical',
            'difficulty': 'medium',
            'question_text': 'Explain Python generators and the yield keyword. How do they help optimize memory usage when processing large datasets?',
            'expected_concepts': ['yield pauses execution and maintains state', 'lazy evaluation / iteration on demand', 'does not store entire collection in memory', 'generator object implements iterator protocol'],
            'reference_answer': 'Generators are functions that produce a sequence of values lazily using the yield statement instead of return. When yield is encountered, function execution is paused and its local state is preserved. This allows processing potentially infinite or very large streams of data without storing the entire dataset in RAM, yielding O(1) memory complexity.',
            'rubric': {'correctness': 0.35, 'conceptual_understanding': 0.35, 'clarity': 0.30}
        },
        {
            'role_slug': 'python-developer',
            'skill_slug': 'python',
            'question_type': 'technical',
            'difficulty': 'medium',
            'question_text': 'What is the Global Interpreter Lock (GIL) in CPython, and what are its implications for CPU-bound versus I/O-bound multithreaded tasks?',
            'expected_concepts': ['CPython mutex preventing multiple native threads from executing Python bytecode simultaneously', 'thread safety for reference counting', 'CPU-bound concurrency requires multiprocessing', 'I/O-bound tasks release GIL during I/O'],
            'reference_answer': 'The Global Interpreter Lock (GIL) is a mutex used by CPython to ensure only one thread executes Python bytecode at a time, protecting internal reference count memory management. Consequently, standard multithreading cannot achieve true CPU parallelism across multiple cores for CPU-bound tasks (which requires the multiprocessing module). However, for I/O-bound operations (network, disk, DB queries), threads release the GIL while waiting, making multithreading or asyncio effective.',
            'rubric': {'correctness': 0.40, 'reasoning': 0.30, 'clarity': 0.30}
        },
        {
            'role_slug': 'python-developer',
            'skill_slug': 'python',
            'question_type': 'code-written',
            'difficulty': 'medium',
            'question_text': 'Write a Python function `chunk_list(data: list, size: int) -> list` that divides a list into consecutive sublists of maximum length `size`. Explain your approach and handle edge cases (empty list, size <= 0).',
            'expected_concepts': ['validation of size > 0', 'slicing or loop with step', 'range(0, len(data), size)', 'correct return list of lists', 'edge case handling'],
            'reference_answer': 'def chunk_list(data, size):\n    if size <= 0:\n        raise ValueError("Chunk size must be positive")\n    if not data:\n        return []\n    return [data[i:i + size] for i in range(0, len(data), size)]\n\nThe approach uses list slicing with a stepped range to create chunks efficiently in O(N) time.',
            'rubric': {'correctness': 0.40, 'edge_cases': 0.30, 'code_quality': 0.30}
        },
        {
            'role_slug': 'python-developer',
            'skill_slug': 'python',
            'question_type': 'technical',
            'difficulty': 'hard',
            'question_text': 'Explain how Python decorators work under the hood. Describe how functools.wraps is used to preserve function metadata.',
            'expected_concepts': ['first-class functions / closures', 'higher-order function taking a function and returning a wrapper', 'syntactic sugar @decorator', 'functools.wraps updates __name__, __doc__, __annotations__'],
            'reference_answer': 'In Python, functions are first-class objects. A decorator is a higher-order function that takes a callable as an argument, wraps it inside an inner function that adds behavior before or after invocation, and returns the wrapper. The @decorator syntax is syntactic sugar for func = decorator(func). Without functools.wraps, the decorated function loses its original identity, __name__, and docstring; @wraps copies this metadata from the wrapped function to the wrapper.',
            'rubric': {'correctness': 0.35, 'conceptual_understanding': 0.35, 'clarity': 0.30}
        },
        {
            'role_slug': 'python-developer',
            'skill_slug': 'python',
            'question_type': 'technical',
            'difficulty': 'hard',
            'question_text': 'Explain Python memory management: how does CPython combine reference counting with a generational garbage collector to detect cyclical references?',
            'expected_concepts': ['reference counting as primary mechanism', 'deallocation when ref count reaches zero', 'generational cyclic garbage collection (Gen 0, 1, 2)', 'detecting isolated cycles of unreachable objects'],
            'reference_answer': 'CPython uses reference counting as its primary memory management technique: every object tracks how many references point to it, and when the count drops to zero, its memory is immediately deallocated. Because reference counting cannot detect circular references (e.g., Object A references B and B references A), Python includes a generational cyclic garbage collector that tracks container objects across three generations, periodically traversing pointer graphs to find unreachable cycles.',
            'rubric': {'correctness': 0.40, 'depth': 0.35, 'clarity': 0.25}
        },
        {
            'role_slug': 'python-developer',
            'skill_slug': 'python',
            'question_type': 'code-written',
            'difficulty': 'hard',
            'question_text': 'Write a Python context manager using a class with `__enter__` and `__exit__` to measure and print the execution time of a code block. Explain exception propagation in `__exit__`.',
            'expected_concepts': ['__enter__ returns resource or records start time', '__exit__ receives exc_type, exc_val, exc_tb', 'returning True suppresses exceptions, returning False or None propagates them', 'time.perf_counter'],
            'reference_answer': 'import time\n\nclass Timer:\n    def __enter__(self):\n        self.start = time.perf_counter()\n        return self\n    def __exit__(self, exc_type, exc_val, exc_tb):\n        self.elapsed = time.perf_counter() - self.start\n        print(f"Elapsed: {self.elapsed:.4f}s")\n        return False  # Do not suppress exceptions\n\nReturning False from __exit__ guarantees that any unhandled exception inside the with-block propagates upward.',
            'rubric': {'correctness': 0.40, 'exception_handling': 0.30, 'code_quality': 0.30}
        },

        # Skill: Object-Oriented Programming (OOP) (8 questions)
        {
            'role_slug': 'python-developer',
            'skill_slug': 'oop',
            'question_type': 'technical',
            'difficulty': 'easy',
            'question_text': 'Define the four core pillars of Object-Oriented Programming: Encapsulation, Abstraction, Inheritance, and Polymorphism.',
            'expected_concepts': ['encapsulation bundles data and methods restricting direct access', 'abstraction hides internal complexity showing essential features', 'inheritance allows child classes to derive properties from parents', 'polymorphism enables different classes to respond to the same interface'],
            'reference_answer': '1. Encapsulation: Bundles data and the methods operating on that data within a class while restricting direct access to internal state. 2. Abstraction: Hides intricate implementation details and exposes only essential operations through interfaces. 3. Inheritance: Enables code reusability by deriving new classes from existing parent classes. 4. Polymorphism: Allows entities to take multiple forms, enabling different classes to implement common interfaces with class-specific behavior.',
            'rubric': {'correctness': 0.40, 'completeness': 0.30, 'clarity': 0.30}
        },
        {
            'role_slug': 'python-developer',
            'skill_slug': 'oop',
            'question_type': 'technical',
            'difficulty': 'easy',
            'question_text': 'What is method overloading versus method overriding? How do they relate to compile-time and runtime polymorphism?',
            'expected_concepts': ['overloading is multiple methods with same name but different signatures', 'overriding is subclass providing specific implementation of inherited method', 'overloading is static/compile-time polymorphism', 'overriding is dynamic/runtime polymorphism'],
            'reference_answer': 'Method overloading allows a class to have multiple methods with the same name but different parameters (types or counts), resolved at compile time (static polymorphism). Method overriding occurs when a subclass redefines a method declared in its parent with the identical signature, resolved at runtime through virtual method dispatch (dynamic polymorphism).',
            'rubric': {'correctness': 0.40, 'distinction': 0.30, 'clarity': 0.30}
        },
        {
            'role_slug': 'python-developer',
            'skill_slug': 'oop',
            'question_type': 'technical',
            'difficulty': 'medium',
            'question_text': 'Explain the difference between Composition and Inheritance. Why is the design principle "Favor composition over inheritance" widely recommended?',
            'expected_concepts': ['inheritance represents IS-A relationship', 'composition represents HAS-A relationship', 'tight coupling in inheritance', 'flexibility and loose coupling in composition', 'runtime behavior modification'],
            'reference_answer': 'Inheritance represents an "is-a" relationship where a subclass is tightly coupled to the internal details and hierarchy of its parent. Composition represents a "has-a" relationship where an object contains references to other objects to delegate behavior. "Favor composition over inheritance" is recommended because composition reduces brittle coupling, allows dynamic swapping of implementations at runtime, and prevents deep inheritance trees.',
            'rubric': {'correctness': 0.35, 'reasoning': 0.35, 'clarity': 0.30}
        },
        {
            'role_slug': 'python-developer',
            'skill_slug': 'oop',
            'question_type': 'technical',
            'difficulty': 'medium',
            'question_text': 'Explain the Single Responsibility Principle (SRP) and Open/Closed Principle (OCP) from SOLID design principles with concrete software examples.',
            'expected_concepts': ['SRP: a class should have one and only one reason to change', 'OCP: software entities should be open for extension but closed for modification', 'refactoring example with separate persistence vs presentation', 'extending through interfaces or subclasses'],
            'reference_answer': 'Single Responsibility Principle states that a module or class should have only one reason to change, meaning it addresses a single concern (e.g., separating user authentication logic from email formatting). Open/Closed Principle states that classes should be open for extension but closed for modification, meaning new features should be added by implementing new classes or interfaces rather than editing tested legacy code.',
            'rubric': {'correctness': 0.40, 'examples': 0.30, 'clarity': 0.30}
        },
        {
            'role_slug': 'python-developer',
            'skill_slug': 'oop',
            'question_type': 'code-written',
            'difficulty': 'medium',
            'question_text': 'Write a class hierarchy in Python or Java modeling a PaymentProcessor interface with two implementations: CreditCardPayment and UpiPayment. Demonstrate polymorphic payment execution.',
            'expected_concepts': ['base abstract class or interface with process_payment method', 'concrete class CreditCardPayment', 'concrete class UpiPayment', 'polymorphic client function accepting base type'],
            'reference_answer': 'from abc import ABC, abstractmethod\n\nclass PaymentProcessor(ABC):\n    @abstractmethod\n    def pay(self, amount: float) -> bool:\n        pass\n\nclass CreditCardPayment(PaymentProcessor):\n    def pay(self, amount: float) -> bool:\n        print(f"Charged ${amount} to Credit Card")\n        return True\n\nclass UpiPayment(PaymentProcessor):\n    def pay(self, amount: float) -> bool:\n        print(f"Processed UPI transfer of ${amount}")\n        return True\n\ndef checkout(processor: PaymentProcessor, amount: float):\n    return processor.pay(amount)',
            'rubric': {'correctness': 0.40, 'polymorphism': 0.30, 'code_quality': 0.30}
        },
        {
            'role_slug': 'python-developer',
            'skill_slug': 'oop',
            'question_type': 'technical',
            'difficulty': 'hard',
            'question_text': 'What is the Liskov Substitution Principle (LSP)? Describe a common violation (such as the classic Rectangle vs Square problem) and how to fix it.',
            'expected_concepts': ['subtypes must be substitutable for their base types without altering program correctness', 'Square inheriting from Rectangle violates contracts of setWidth/setHeight', 'preconditions cannot be strengthened and postconditions cannot be weakened in subtype', 'solution: separate shapes or make immutable'],
            'reference_answer': 'LSP asserts that objects of a superclass should be replaceable with objects of a subclass without breaking application correctness. The Rectangle/Square example violates LSP if Square inherits from Rectangle: setting width on a Square unexpectedly mutates height, violating callers expectations of Rectangle behavior. To fix this, both Rectangle and Square should implement an abstract Shape interface with an area() method, rather than inheriting from one another.',
            'rubric': {'correctness': 0.40, 'reasoning': 0.35, 'clarity': 0.25}
        },
        {
            'role_slug': 'python-developer',
            'skill_slug': 'oop',
            'question_type': 'technical',
            'difficulty': 'hard',
            'question_text': 'Explain the Dependency Inversion Principle (DIP). How does Dependency Injection (DI) implement DIP, and what are the architectural benefits for testing?',
            'expected_concepts': ['high-level modules should not depend on low-level modules, both depend on abstractions', 'abstractions should not depend on details', 'DI injects dependencies from outside rather than instantiating internally', 'mocking and unit test isolation'],
            'reference_answer': 'DIP states that high-level business modules should not depend on low-level modules (such as specific database drivers); both should depend on abstractions. Dependency Injection is a pattern that realizes DIP by passing dependencies into an object via constructor or setter rather than letting the object instantiate them directly. This decouples classes and allows easy replacement with test doubles/mocks during unit testing.',
            'rubric': {'correctness': 0.40, 'architectural_depth': 0.35, 'clarity': 0.25}
        },
        {
            'role_slug': 'python-developer',
            'skill_slug': 'oop',
            'question_type': 'code-written',
            'difficulty': 'hard',
            'question_text': 'Implement a thread-safe Singleton pattern in Python or Java. Explain why naive singletons fail in multi-threaded environments and how double-checked locking works.',
            'expected_concepts': ['private constructor or __new__ override', 'synchronization / threading.Lock', 'double-checked locking pattern checking instance before and inside lock', 'thread safety'],
            'reference_answer': 'import threading\n\nclass ThreadSafeSingleton:\n    _instance = None\n    _lock = threading.Lock()\n\n    def __new__(cls):\n        if cls._instance is None:\n            with cls._lock:\n                if cls._instance is None:\n                    cls._instance = super().__new__(cls)\n        return cls._instance\n\nNaive singletons fail because two threads can simultaneously pass the "if instance is None" check and create two instances. Double-checked locking prevents performance degradation by only locking on the first creation.',
            'rubric': {'correctness': 0.40, 'thread_safety': 0.35, 'code_quality': 0.25}
        },

        # Skill: Flask (8 questions)
        {
            'role_slug': 'python-developer',
            'skill_slug': 'flask',
            'question_type': 'technical',
            'difficulty': 'easy',
            'question_text': 'What is the WSGI standard in Python web development, and what role does it play in a Flask application?',
            'expected_concepts': ['Web Server Gateway Interface', 'standard interface between Python web applications and web servers', 'Flask application is a callable WSGI application', 'servers like Gunicorn or uWSGI'],
            'reference_answer': 'WSGI (Web Server Gateway Interface, PEP 3333) is the specification defining how web servers (e.g., Gunicorn, Nginx via uWSGI) communicate with Python web applications. A Flask application instance is a WSGI-compliant callable that accepts environ and start_response arguments, ensuring framework interoperability with web servers.',
            'rubric': {'correctness': 0.40, 'completeness': 0.30, 'clarity': 0.30}
        },
        {
            'role_slug': 'python-developer',
            'skill_slug': 'flask',
            'question_type': 'technical',
            'difficulty': 'easy',
            'question_text': 'Explain the difference between Flask URL routing parameters `<string:name>` and `<int:id>`. What happens if a non-integer is passed to `<int:id>`?',
            'expected_concepts': ['URL converters / route variables', 'string matches any text without slashes', 'int converts parameter to Python integer', 'returns 404 Not Found if converter validation fails'],
            'reference_answer': 'Flask route converters parse and cast variable components of the URL path. `<string:name>` accepts any text without slashes and passes it as a string. `<int:id>` ensures that the segment contains digits, converts it to an integer, and passes it to the view function; if a non-integer is supplied in the URL, Flask automatically rejects the request with a 404 Not Found error.',
            'rubric': {'correctness': 0.40, 'completeness': 0.30, 'clarity': 0.30}
        },
        {
            'role_slug': 'python-developer',
            'skill_slug': 'flask',
            'question_type': 'technical',
            'difficulty': 'medium',
            'question_text': 'Explain the Flask Application Factory pattern (`create_app()`). Why is it considered best practice over a single global `app = Flask(__name__)`?',
            'expected_concepts': ['create_app function instantiating and configuring app', 'enables multiple instances with different configurations (test, dev, prod)', 'prevents circular import dependencies', 'simplifies test isolation'],
            'reference_answer': 'The Application Factory pattern involves defining a function (typically `create_app(config_name)`) that creates, configures, and registers blueprints/extensions on a new Flask instance. This is best practice because it allows creating isolated instances for testing, running different configurations without altering global state, and breaking circular imports between routes and models.',
            'rubric': {'correctness': 0.40, 'reasoning': 0.30, 'clarity': 0.30}
        },
        {
            'role_slug': 'python-developer',
            'skill_slug': 'flask',
            'question_type': 'technical',
            'difficulty': 'medium',
            'question_text': 'What are Flask Blueprints, and how do they help structure scalable web applications?',
            'expected_concepts': ['modular component grouping routes, templates, and static files', 'registered onto the main application with url_prefix', 'separation of concerns (e.g. auth, api, admin)', 'reusability and team collaboration'],
            'reference_answer': 'Blueprints are Flask objects that group related routes, error handlers, static files, and templates into self-contained architectural modules (such as auth, admin, api). Instead of registering routes directly on the global app, blueprints are defined independently and registered onto the app factory with dedicated URL prefixes, facilitating modularity and clean separation of concerns.',
            'rubric': {'correctness': 0.40, 'structure': 0.30, 'clarity': 0.30}
        },
        {
            'role_slug': 'python-developer',
            'skill_slug': 'flask',
            'question_type': 'code-written',
            'difficulty': 'medium',
            'question_text': 'Write a Flask REST API endpoint `/api/items` that handles `POST` requests. Validate that the JSON body contains a `name` (string) and `price` (positive float). Return proper HTTP status codes and JSON responses.',
            'expected_concepts': ['request.get_json()', 'validation of missing fields and data types', 'price > 0 check', 'status 201 Created on success', 'status 400 Bad Request on invalid input'],
            'reference_answer': 'from flask import Blueprint, request, jsonify\n\napi_bp = Blueprint("api", __name__)\n\n@api_bp.route("/api/items", methods=["POST"])\ndef create_item():\n    data = request.get_json(silent=True)\n    if not data or "name" not in data or "price" not in data:\n        return jsonify({"error": "Missing name or price"}), 400\n    if not isinstance(data["name"], str) or not data["name"].strip():\n        return jsonify({"error": "Invalid name"}), 400\n    try:\n        price = float(data["price"])\n        if price <= 0:\n            raise ValueError()\n    except (ValueError, TypeError):\n        return jsonify({"error": "Price must be a positive number"}), 400\n    return jsonify({"message": "Item created", "item": {"name": data["name"].strip(), "price": price}}), 201',
            'rubric': {'correctness': 0.40, 'validation': 0.35, 'http_codes': 0.25}
        },
        {
            'role_slug': 'python-developer',
            'skill_slug': 'flask',
            'question_type': 'technical',
            'difficulty': 'hard',
            'question_text': 'Explain the Flask Application Context vs Request Context. What are `current_app`, `g`, `request`, and `session`, and how are context locals thread-safe?',
            'expected_concepts': ['Request Context manages request and session', 'Application Context manages current_app and g', 'Context locals (Werkzeug LocalProxy) bound to current execution thread or async greenlet', 'popping contexts after request finishes'],
            'reference_answer': 'Flask uses two context layers: the Application Context (binding `current_app` and request-scoped storage `g`) and the Request Context (binding `request` and `session`). Behind the scenes, these proxies use Werkzeug context locals (or contextvars in modern Python), ensuring that concurrent requests in different threads or worker tasks access their own isolated context without data pollution.',
            'rubric': {'correctness': 0.40, 'depth': 0.35, 'clarity': 0.25}
        },
        {
            'role_slug': 'python-developer',
            'skill_slug': 'flask',
            'question_type': 'technical',
            'difficulty': 'hard',
            'question_text': 'Describe how CSRF (Cross-Site Request Forgery) attacks occur and how Flask-WTF protects state-changing forms and AJAX requests.',
            'expected_concepts': ['malicious site inducing user browser to send authenticated requests via session cookies', 'SameSite cookie limitations', 'Flask-WTF synchronizer token pattern', 'validating csrf_token in hidden form field or X-CSRFToken header'],
            'reference_answer': 'CSRF occurs when a malicious website tricks a logged-in user browser into executing unwanted actions on a trusted site by relying on automatic session cookie transmission. Flask-WTF mitigates this using the synchronizer token pattern: it embeds a unique, cryptographically signed token into user sessions and requires this token in a hidden form field or X-CSRFToken request header on state-changing methods (POST, PUT, DELETE).',
            'rubric': {'correctness': 0.40, 'security_depth': 0.35, 'clarity': 0.25}
        },
        {
            'role_slug': 'python-developer',
            'skill_slug': 'flask',
            'question_type': 'code-written',
            'difficulty': 'hard',
            'question_text': 'Write a custom Flask decorator `@token_required` that inspects the `Authorization: Bearer <token>` header, verifies a mock token string, attaches user data to `request.user` or Flask `g`, and returns 401 if missing or invalid.',
            'expected_concepts': ['functools.wraps', 'request.headers.get("Authorization")', 'Bearer prefix splitting', 'attaching user to g.current_user or aborting 401', 'invoking original view function'],
            'reference_answer': 'from functools import wraps\nfrom flask import request, jsonify, g\n\ndef token_required(f):\n    @wraps(f)\n    def decorated(*args, **kwargs):\n        auth_header = request.headers.get("Authorization", "")\n        if not auth_header or not auth_header.startswith("Bearer "):\n            return jsonify({"error": "Missing or malformed Authorization header"}), 401\n        token = auth_header.split(" ")[1]\n        if token != "valid-secret-token":  # Simulated verification\n            return jsonify({"error": "Invalid or expired token"}), 401\n        g.current_user = {"user_id": 42, "role": "candidate"}\n        return f(*args, **kwargs)\n    return decorated',
            'rubric': {'correctness': 0.40, 'security_handling': 0.35, 'code_quality': 0.25}
        },

        # Skill: SQL & Relational Databases (8 questions)
        {
            'role_slug': 'python-developer',
            'skill_slug': 'sql',
            'question_type': 'technical',
            'difficulty': 'easy',
            'question_text': 'Explain the difference between INNER JOIN, LEFT JOIN, and RIGHT JOIN with an example using Users and Orders tables.',
            'expected_concepts': ['INNER JOIN returns rows where match exists in both tables', 'LEFT JOIN returns all rows from left table and matching from right', 'RIGHT JOIN returns all rows from right table and matching from left', 'NULL values for unmatched rows'],
            'reference_answer': 'INNER JOIN returns only records where matching foreign keys exist in both tables (e.g., users who placed orders). LEFT JOIN returns all rows from the left table (Users) plus matching rows from the right (Orders); if a user has no orders, order columns are NULL. RIGHT JOIN returns all orders and matching users.',
            'rubric': {'correctness': 0.40, 'examples': 0.30, 'clarity': 0.30}
        },
        {
            'role_slug': 'python-developer',
            'skill_slug': 'sql',
            'question_type': 'technical',
            'difficulty': 'easy',
            'question_text': 'What is the purpose of database normalization? Briefly contrast 1NF, 2NF, and 3NF.',
            'expected_concepts': ['reducing data redundancy and preventing anomalies (insert, update, delete)', '1NF: atomic values and no repeating groups', '2NF: 1NF plus no partial dependencies on composite PK', '3NF: 2NF plus no transitive dependencies'],
            'reference_answer': 'Database normalization organizes schema columns and tables to eliminate data redundancy and prevent insertion, update, and deletion anomalies. 1NF requires atomic column values and unique rows. 2NF requires 1NF and guarantees all non-key attributes are fully functionally dependent on the primary key (no partial dependencies). 3NF requires 2NF and removes transitive dependencies (non-key columns depending on other non-key columns).',
            'rubric': {'correctness': 0.40, 'forms_explanation': 0.30, 'clarity': 0.30}
        },
        {
            'role_slug': 'python-developer',
            'skill_slug': 'sql',
            'question_type': 'technical',
            'difficulty': 'medium',
            'question_text': 'Explain the ACID properties of relational transactions and their role in ensuring database consistency.',
            'expected_concepts': ['Atomicity (all or nothing)', 'Consistency (database remains in valid state satisfying constraints)', 'Isolation (concurrent transactions do not interfere)', 'Durability (committed data survives system crashes)'],
            'reference_answer': 'ACID guarantees database transaction reliability: Atomicity ensures all operations in a transaction succeed together or all roll back completely. Consistency ensures transactions transition the database only between states that satisfy all schema constraints and foreign keys. Isolation ensures concurrently executing transactions do not interfere with one another. Durability guarantees that committed data survives power failures or system crashes.',
            'rubric': {'correctness': 0.40, 'conceptual_understanding': 0.35, 'clarity': 0.25}
        },
        {
            'role_slug': 'python-developer',
            'skill_slug': 'sql',
            'question_type': 'code-written',
            'difficulty': 'medium',
            'question_text': 'Given tables `employees (id, name, department_id, salary)` and `departments (id, name)`, write an SQL query to find the department name and highest salary in each department having more than 3 employees.',
            'expected_concepts': ['JOIN departments and employees', 'GROUP BY department name', 'MAX(salary)', 'HAVING COUNT(employees.id) > 3'],
            'reference_answer': 'SELECT d.name AS department_name, MAX(e.salary) AS highest_salary\nFROM departments d\nINNER JOIN employees e ON d.id = e.department_id\nGROUP BY d.id, d.name\nHAVING COUNT(e.id) > 3;',
            'rubric': {'correctness': 0.40, 'group_by_having': 0.35, 'syntax': 0.25}
        },
        {
            'role_slug': 'python-developer',
            'skill_slug': 'sql',
            'question_type': 'technical',
            'difficulty': 'medium',
            'question_text': 'Explain B-Tree indexing in relational databases. What are clustered vs non-clustered indexes, and when can indexing hurt performance?',
            'expected_concepts': ['B-Tree allows O(log N) lookup, insertion, and range queries', 'clustered index determines physical sorting order of table rows (one per table)', 'non-clustered index stores separate pointer structure', 'write overhead on INSERT/UPDATE/DELETE'],
            'reference_answer': 'A B-Tree index is a balanced tree data structure that enables fast logarithmic lookups, range searches, and sequential access. A clustered index defines the physical order of data on disk (usually the primary key, one per table). Non-clustered indexes store copies of indexed column values alongside pointers to physical rows. While indexes drastically accelerate SELECT queries, excessive indexing degrades INSERT, UPDATE, and DELETE write performance.',
            'rubric': {'correctness': 0.40, 'reasoning': 0.30, 'clarity': 0.30}
        },
        {
            'role_slug': 'python-developer',
            'skill_slug': 'sql',
            'question_type': 'technical',
            'difficulty': 'hard',
            'question_text': 'Explain SQL transaction isolation levels: Read Uncommitted, Read Committed, Repeatable Read, and Serializable. What phenomena do they prevent (dirty reads, non-repeatable reads, phantom reads)?',
            'expected_concepts': ['dirty reads (reading uncommitted changes)', 'non-repeatable reads (re-reading same row gets different data)', 'phantom reads (new rows appearing in range query)', 'mapping levels to prevented phenomena', 'locks vs MVCC'],
            'reference_answer': 'Isolation levels balance concurrency against data anomalies: 1. Read Uncommitted allows dirty reads. 2. Read Committed prevents dirty reads but permits non-repeatable reads. 3. Repeatable Read (default in MySQL InnoDB) prevents dirty and non-repeatable reads, and prevents phantom reads using next-key locking. 4. Serializable completely isolates transactions sequentially, preventing all three anomalies at the expense of higher lock contention.',
            'rubric': {'correctness': 0.40, 'depth': 0.35, 'clarity': 0.25}
        },
        {
            'role_slug': 'python-developer',
            'skill_slug': 'sql',
            'question_type': 'code-written',
            'difficulty': 'hard',
            'question_text': 'Write an SQL query using a Window Function (`DENSE_RANK()` or `ROW_NUMBER()`) to find the top 2 highest-earning employees in each department from table `employees (id, name, department_id, salary)`.',
            'expected_concepts': ['CTE or subquery with OVER clause', 'PARTITION BY department_id', 'ORDER BY salary DESC', 'filtering ranking <= 2 in outer query'],
            'reference_answer': 'WITH RankedEmployees AS (\n    SELECT id, name, department_id, salary,\n           DENSE_RANK() OVER (PARTITION BY department_id ORDER BY salary DESC) AS salary_rank\n    FROM employees\n)\nSELECT id, name, department_id, salary\nFROM RankedEmployees\nWHERE salary_rank <= 2;',
            'rubric': {'correctness': 0.45, 'window_function_usage': 0.35, 'code_quality': 0.20}
        },
        {
            'role_slug': 'python-developer',
            'skill_slug': 'sql',
            'question_type': 'technical',
            'difficulty': 'hard',
            'question_text': 'How do you analyze a slow SQL query using `EXPLAIN` or `EXPLAIN ANALYZE`? What indicators (e.g., `type=ALL`, filesort, temporary table) signal critical performance bottlenecks?',
            'expected_concepts': ['EXPLAIN shows query execution plan', 'type=ALL indicates full table scan', 'key=NULL means no index was used', 'Using filesort / Using temporary indicates disk/memory sorting bottlenecks', 'rows examined vs rows returned'],
            'reference_answer': '`EXPLAIN` outputs the query execution plan chosen by the optimizer. Warning flags include: `type=ALL` (a full table scan inspecting every row), `key=NULL` (no index utilized), `Using filesort` (the engine must sort rows outside of an index), and `Using temporary` (MySQL creates an in-memory/disk temporary table for aggregations). Fixing these usually involves creating composite indexes matching WHERE, JOIN, and ORDER BY columns.',
            'rubric': {'correctness': 0.40, 'practical_indicators': 0.35, 'clarity': 0.25}
        },

        # Skill: Java (8 questions)
        {
            'role_slug': 'java-developer',
            'skill_slug': 'java',
            'question_type': 'technical',
            'difficulty': 'easy',
            'question_text': 'Explain the difference between `==` and the `.equals()` method in Java. How should string comparisons be handled?',
            'expected_concepts': ['== compares object memory references', '.equals() compares logical object state / value equality', 'String pool mechanism', 'always using .equals() or Objects.equals() for string content comparison'],
            'reference_answer': 'In Java, `==` compares primitive values or reference equality (whether two variables point to the exact same memory address). The `.equals()` method checks logical content equality. Because Java uses a string constant pool, string literals might share references, but newly allocated Strings will not; therefore, `.equals()` or `Objects.equals(a, b)` should always be used to compare String content.',
            'rubric': {'correctness': 0.40, 'completeness': 0.30, 'clarity': 0.30}
        },
        {
            'role_slug': 'java-developer',
            'skill_slug': 'java',
            'question_type': 'technical',
            'difficulty': 'easy',
            'question_text': 'What is the Java Virtual Machine (JVM), and how does Java achieve "Write Once, Run Anywhere" (WORA)?',
            'expected_concepts': ['Java source code compiles to platform-independent bytecode (.class)', 'JVM interprets or JIT-compiles bytecode into native machine instructions', 'platform-specific JVM implementations'],
            'reference_answer': 'Java achieves WORA by compiling `.java` source code into intermediate, platform-neutral bytecode (`.class` files) via javac. The Java Virtual Machine (JVM) is installed specifically for each target operating system and translates or compiles (via JIT) this bytecode into native machine instructions at runtime.',
            'rubric': {'correctness': 0.40, 'conceptual_understanding': 0.30, 'clarity': 0.30}
        },
        {
            'role_slug': 'java-developer',
            'skill_slug': 'java',
            'question_type': 'technical',
            'difficulty': 'medium',
            'question_text': 'Explain the contract between `equals()` and `hashCode()` in Java. What happens when `equals()` is overridden without overriding `hashCode()` in a `HashSet` or `HashMap`?',
            'expected_concepts': ['if two objects are equal by equals(), they must produce the same hashCode()', 'hash buckets in HashMap/HashSet', 'failing to override hashCode causes duplicate entries or failed lookups in hash-based collections'],
            'reference_answer': 'The contract dictates that if `o1.equals(o2)` is true, then `o1.hashCode() == o2.hashCode()` must also be true. If `equals()` is overridden but `hashCode()` is not, two logically equal objects will yield different hash codes, causing `HashMap` and `HashSet` to place them into different hash buckets. As a result, `map.get()` will fail to retrieve values stored under equal keys.',
            'rubric': {'correctness': 0.40, 'reasoning': 0.30, 'clarity': 0.30}
        },
        {
            'role_slug': 'java-developer',
            'skill_slug': 'java',
            'question_type': 'technical',
            'difficulty': 'medium',
            'question_text': 'Explain the difference between `ArrayList` and `LinkedList` in Java regarding internal structure, time complexity of common operations, and memory efficiency.',
            'expected_concepts': ['ArrayList backed by dynamic resizable array, O(1) random access', 'LinkedList backed by doubly linked list, O(N) access by index, O(1) insertion/deletion at nodes', 'memory overhead of Node references in LinkedList', 'cache locality favors ArrayList'],
            'reference_answer': '`ArrayList` uses a contiguous dynamic array, offering O(1) random access by index and excellent CPU cache locality, but requiring O(N) worst-case shifts for middle insertions. `LinkedList` is a doubly linked list offering O(1) head/tail insertions and deletions once a node is reached, but O(N) search by index. `ArrayList` is almost always preferred in modern Java due to cache friendliness and lower memory overhead.',
            'rubric': {'correctness': 0.40, 'complexity_comparison': 0.30, 'clarity': 0.30}
        },
        {
            'role_slug': 'java-developer',
            'skill_slug': 'java',
            'question_type': 'code-written',
            'difficulty': 'medium',
            'question_text': 'Write a Java method using the Streams API to filter a list of strings: keep only strings with length > 3, convert them to uppercase, sort them alphabetically, and collect into a List. Handle null inputs gracefully.',
            'expected_concepts': ['null check', 'list.stream()', 'filter(s -> s != null && s.length() > 3)', 'map(String::toUpperCase)', 'sorted()', 'collect(Collectors.toList())'],
            'reference_answer': 'import java.util.*;\nimport java.util.stream.Collectors;\n\npublic class StreamExample {\n    public static List<String> processStrings(List<String> input) {\n        if (input == null) return Collections.emptyList();\n        return input.stream()\n            .filter(s -> s != null && s.length() > 3)\n            .map(String::toUpperCase)\n            .sorted()\n            .collect(Collectors.toList());\n    }\n}',
            'rubric': {'correctness': 0.40, 'streams_syntax': 0.35, 'null_safety': 0.25}
        },
        {
            'role_slug': 'java-developer',
            'skill_slug': 'java',
            'question_type': 'technical',
            'difficulty': 'hard',
            'question_text': 'Explain Java Memory Model (JMM): differentiate Heap, Stack, and Metaspace. How does the `volatile` keyword ensure visibility and prevent instruction reordering?',
            'expected_concepts': ['Stack stores thread execution frames and local primitives/references', 'Heap stores all instantiated objects', 'Metaspace stores class metadata and bytecode', 'volatile guarantees immediate visibility across threads without CPU caching', 'prevents compiler/CPU reordering via memory barriers'],
            'reference_answer': 'The Stack allocates thread-local call frames, local variables, and object references with automatic push/pop lifecycle. The Heap houses all dynamically instantiated objects managed by garbage collection. Metaspace stores loaded class metadata outside the heap in native OS memory. The `volatile` keyword guarantees that writes to a variable are immediately flushed to main memory and subsequent reads fetch from main memory (preventing CPU register caching), while establishing memory barriers that prevent compiler and hardware instruction reordering.',
            'rubric': {'correctness': 0.40, 'jmm_depth': 0.35, 'clarity': 0.25}
        },
        {
            'role_slug': 'java-developer',
            'skill_slug': 'java',
            'question_type': 'technical',
            'difficulty': 'hard',
            'question_text': 'Explain Java multithreading synchronization mechanisms: synchronized keyword, ReentrantLock, and ConcurrentHashMap. How does ConcurrentHashMap avoid blocking entire collections?',
            'expected_concepts': ['synchronized uses intrinsic monitor lock', 'ReentrantLock provides explicit lock/unlock, tryLock with timeout, fairness', 'ConcurrentHashMap uses bucket-level synchronization (CAS and synchronized on node heads)', 'striped / bucket concurrency vs monolithic table lock'],
            'reference_answer': '`synchronized` locks an objects intrinsic monitor, blocking competing threads. `ReentrantLock` offers advanced concurrency with interruptible lock acquisitions, timeouts (`tryLock`), and fair queueing. `ConcurrentHashMap` avoids monolithic locking by using lock-free Compare-And-Swap (CAS) for empty bucket insertions and fine-grained locks on only the head node of a hash bucket during write collisions, allowing concurrent readers and writers across different buckets.',
            'rubric': {'correctness': 0.40, 'concurrency_depth': 0.35, 'clarity': 0.25}
        },
        {
            'role_slug': 'java-developer',
            'skill_slug': 'java',
            'question_type': 'code-written',
            'difficulty': 'hard',
            'question_text': 'Implement a thread-safe bounded Producer-Consumer pattern in Java using `ReentrantLock` and two `Condition` variables (notFull and notEmpty) or `BlockingQueue`.',
            'expected_concepts': ['bounded buffer queue', 'ReentrantLock instance', 'Condition notFull and notEmpty', 'await() while buffer is full/empty', 'signal() or signalAll() when state changes'],
            'reference_answer': 'import java.util.LinkedList;\nimport java.util.Queue;\nimport java.util.concurrent.locks.*;\n\npublic class BoundedBuffer<T> {\n    private final Queue<T> queue = new LinkedList<>();\n    private final int capacity;\n    private final Lock lock = new ReentrantLock();\n    private final Condition notFull = lock.newCondition();\n    private final Condition notEmpty = lock.newCondition();\n\n    public BoundedBuffer(int capacity) { this.capacity = capacity; }\n\n    public void put(T item) throws InterruptedException {\n        lock.lock();\n        try {\n            while (queue.size() == capacity) notFull.await();\n            queue.add(item);\n            notEmpty.signal();\n        } finally { lock.unlock(); }\n    }\n\n    public T take() throws InterruptedException {\n        lock.lock();\n        try {\n            while (queue.isEmpty()) notEmpty.await();\n            T item = queue.poll();\n            notFull.signal();\n            return item;\n        } finally { lock.unlock(); }\n    }\n}',
            'rubric': {'correctness': 0.40, 'thread_synchronization': 0.35, 'code_quality': 0.25}
        },

        # Skill: Spring Boot (8 questions)
        {
            'role_slug': 'java-developer',
            'skill_slug': 'spring-boot',
            'question_type': 'technical',
            'difficulty': 'easy',
            'question_text': 'What is Inversion of Control (IoC) and Dependency Injection (DI) in Spring Boot? How does `@Autowired` work?',
            'expected_concepts': ['IoC delegates object creation and lifecycle management to Spring container', 'DI passes dependencies into beans rather than manual new instantiation', '@Autowired instructs Spring to resolve and inject matching bean by type'],
            'reference_answer': 'Inversion of Control (IoC) is a design architectural pattern where the control of object creation, configuration, and lifecycle is inverted from application code to the Spring IoC Container. Dependency Injection (DI) is the concrete implementation of IoC where dependencies are injected into client classes. `@Autowired` instructs Spring to automatically locate and inject a matching bean by type from the ApplicationContext.',
            'rubric': {'correctness': 0.40, 'completeness': 0.30, 'clarity': 0.30}
        },
        {
            'role_slug': 'java-developer',
            'skill_slug': 'spring-boot',
            'question_type': 'technical',
            'difficulty': 'easy',
            'question_text': 'What is the purpose of the `@SpringBootApplication` annotation? What three annotations does it encompass?',
            'expected_concepts': ['@Configuration (declares beans)', '@EnableAutoConfiguration (configures beans based on classpath dependencies)', '@ComponentScan (scans current and subpackages for @Component, @Service, @Repository, @Controller)'],
            'reference_answer': '`@SpringBootApplication` is a convenience meta-annotation placed on the main entry-point class. It aggregates three essential annotations: 1. `@Configuration` (allows registering extra beans and context configs), 2. `@EnableAutoConfiguration` (tells Spring Boot to auto-configure components based on jar dependencies on the classpath), and 3. `@ComponentScan` (enables automatic component scanning for Spring beans in the current package and subpackages).',
            'rubric': {'correctness': 0.40, 'annotations_explained': 0.35, 'clarity': 0.25}
        },
        {
            'role_slug': 'java-developer',
            'skill_slug': 'spring-boot',
            'question_type': 'technical',
            'difficulty': 'medium',
            'question_text': 'Explain the difference between `@Component`, `@Service`, `@Repository`, and `@Controller` in Spring Boot.',
            'expected_concepts': ['@Component is generic stereotype for any Spring-managed bean', '@Service indicates business logic layer', '@Repository indicates data access layer with automated exception translation', '@Controller/@RestController indicates web presentation layer handling HTTP requests'],
            'reference_answer': 'All four annotations register classes as Spring-managed beans. `@Component` is the root generic stereotype. `@Service` documents that the class holds business domain logic. `@Repository` marks data-access objects and enables automatic persistence exception translation (converting DB exceptions into Spring DataAccessExceptions). `@Controller` (or `@RestController`) handles incoming HTTP endpoints and serializes responses.',
            'rubric': {'correctness': 0.40, 'distinction': 0.35, 'clarity': 0.25}
        },
        {
            'role_slug': 'java-developer',
            'skill_slug': 'spring-boot',
            'question_type': 'technical',
            'difficulty': 'medium',
            'question_text': 'Explain Spring Boot Auto-Configuration and how `@ConditionalOnProperty` or `@ConditionalOnClass` work.',
            'expected_concepts': ['auto-configuration inspects classpath, properties, and beans to automatically configure sensible defaults', 'spring.factories / AutoConfiguration.imports', 'conditional annotations evaluate whether beans should be instantiated'],
            'reference_answer': 'Spring Boot Auto-Configuration scans classpath libraries and property files to automatically initialize and configure standard infrastructure beans (like DataSource, ObjectMapper, or DispatcherServlet) without manual XML or code boilerplate. Conditional annotations like `@ConditionalOnClass` check whether a library exists on the classpath, and `@ConditionalOnProperty` verifies specific config values in application.properties before instantiating the bean.',
            'rubric': {'correctness': 0.40, 'reasoning': 0.30, 'clarity': 0.30}
        },
        {
            'role_slug': 'java-developer',
            'skill_slug': 'spring-boot',
            'question_type': 'code-written',
            'difficulty': 'medium',
            'question_text': 'Write a Spring Boot `@RestController` with an endpoint `GET /api/users/{id}` that uses constructor injection for a `UserService`. Return `200 OK` with user data or `404 Not Found` if missing.',
            'expected_concepts': ['@RestController and @RequestMapping', 'constructor injection with final service field', '@GetMapping("/{id}")', 'ResponseEntity.ok or ResponseEntity.notFound()'],
            'reference_answer': '@RestController\n@RequestMapping("/api/users")\npublic class UserController {\n    private final UserService userService;\n\n    public UserController(UserService userService) {\n        this.userService = userService;\n    }\n\n    @GetMapping("/{id}")\n    public ResponseEntity<UserDto> getUserById(@PathVariable Long id) {\n        return userService.findById(id)\n            .map(ResponseEntity::ok)\n            .orElseGet(() -> ResponseEntity.notFound().build());\n    }\n}',
            'rubric': {'correctness': 0.40, 'constructor_injection': 0.35, 'status_codes': 0.25}
        },
        {
            'role_slug': 'java-developer',
            'skill_slug': 'spring-boot',
            'question_type': 'technical',
            'difficulty': 'hard',
            'question_text': 'How does Spring manage transactions with `@Transactional`? Explain AOP proxying and why calling a `@Transactional` method from within the same class bypasses transaction handling.',
            'expected_concepts': ['Spring creates AOP dynamic proxy (CGLIB or JDK Dynamic Proxy) around transactional beans', 'transaction interceptor opens and commits/rolls back connection', 'self-invocation bypasses proxy calling "this" directly', 'solutions: inject self, refactor to another bean, or use AspectJ bytecode weaving'],
            'reference_answer': 'Spring implements `@Transactional` using Spring AOP proxies: Spring wraps the bean in a proxy that intercepts invocations, begins a transaction via TransactionManager, executes the target method, and commits or rolls back upon runtime exceptions. Self-invocation (calling a transactional method from another method within the same class) bypasses the proxy because the call executes on the raw `this` instance rather than the proxy wrapper, preventing transaction interception.',
            'rubric': {'correctness': 0.40, 'aop_explanation': 0.35, 'clarity': 0.25}
        },
        {
            'role_slug': 'java-developer',
            'skill_slug': 'spring-boot',
            'question_type': 'technical',
            'difficulty': 'hard',
            'question_text': 'What are Spring Bean Scopes? Explain `singleton`, `prototype`, `request`, and `session`. What concurrency issue arises when injecting a prototype bean into a singleton bean?',
            'expected_concepts': ['singleton creates one instance per Spring container', 'prototype creates new instance per injection request', 'request and session bound to HTTP lifecycles', 'injecting prototype into singleton resolves only once at startup unless using @Lookup or ObjectFactory'],
            'reference_answer': 'Standard bean scopes are: `singleton` (default, one instance per Spring container), `prototype` (new instance created upon each request/injection), `request` (one per HTTP request), and `session` (one per user session). When a prototype bean is injected into a singleton bean via constructor or field injection, the prototype is resolved only once during the singleton instantiation, negating the prototype behavior. To obtain a fresh instance every time, one must use method injection (`@Lookup`) or `ObjectFactory<MyPrototypeBean>`.',
            'rubric': {'correctness': 0.40, 'scope_injection_pitfall': 0.35, 'clarity': 0.25}
        },
        {
            'role_slug': 'java-developer',
            'skill_slug': 'spring-boot',
            'question_type': 'code-written',
            'difficulty': 'hard',
            'question_text': 'Implement a global exception handling class in Spring Boot using `@ControllerAdvice` / `@RestControllerAdvice` and `@ExceptionHandler` that catches `ResourceNotFoundException` (returns 404) and generic `Exception` (returns 500) in structured JSON format.',
            'expected_concepts': ['@RestControllerAdvice', '@ExceptionHandler(ResourceNotFoundException.class)', '@ExceptionHandler(Exception.class)', 'structured error response DTO with timestamp, status, error message, path'],
            'reference_answer': 'import org.springframework.http.*;\nimport org.springframework.web.bind.annotation.*;\nimport java.time.LocalDateTime;\nimport java.util.*;\n\n@RestControllerAdvice\npublic class GlobalExceptionHandler {\n    @ExceptionHandler(ResourceNotFoundException.class)\n    public ResponseEntity<Map<String, Object>> handleNotFound(ResourceNotFoundException ex) {\n        Map<String, Object> body = new HashMap<>();\n        body.put("timestamp", LocalDateTime.now());\n        body.put("status", 404);\n        body.put("error", ex.getMessage());\n        return ResponseEntity.status(HttpStatus.NOT_FOUND).body(body);\n    }\n\n    @ExceptionHandler(Exception.class)\n    public ResponseEntity<Map<String, Object>> handleGeneral(Exception ex) {\n        Map<String, Object> body = new HashMap<>();\n        body.put("timestamp", LocalDateTime.now());\n        body.put("status", 500);\n        body.put("error", "An internal server error occurred");\n        return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).body(body);\n    }\n}',
            'rubric': {'correctness': 0.40, 'exception_handlers': 0.35, 'code_quality': 0.25}
        },

        # Skill: Data Analysis & Pandas (8 questions)
        {
            'role_slug': 'data-analyst',
            'skill_slug': 'data-analysis',
            'question_type': 'technical',
            'difficulty': 'easy',
            'question_text': 'Explain the difference between a Pandas Series and a Pandas DataFrame. How are row and column indices structured?',
            'expected_concepts': ['Series is a 1D labeled array with homogeneous data and an index', 'DataFrame is a 2D tabular data structure with labeled rows (index) and columns', 'DataFrame is essentially a collection of aligned Series sharing an index'],
            'reference_answer': 'A Pandas Series is a one-dimensional labeled array capable of holding any data type, accompanied by an explicit index. A Pandas DataFrame is a two-dimensional, size-mutable tabular data structure with labeled axes (rows and columns). A DataFrame can be conceptualized as an ordered dictionary of aligned Series objects sharing the same index.',
            'rubric': {'correctness': 0.40, 'completeness': 0.30, 'clarity': 0.30}
        },
        {
            'role_slug': 'data-analyst',
            'skill_slug': 'data-analysis',
            'question_type': 'technical',
            'difficulty': 'easy',
            'question_text': 'How do you detect and handle missing (null/NaN) values in a Pandas DataFrame? Contrast `dropna()` and `fillna()`.',
            'expected_concepts': ['df.isna() / df.isnull() detection', 'df.dropna() removes rows or columns containing nulls', 'df.fillna() imputes missing values with constant, mean, median, or forward/backward fill', 'trade-offs between data loss and imputation bias'],
            'reference_answer': 'Missing values are detected using `df.isna()` or `df.isnull()`, often chained with `.sum()`. `df.dropna()` removes rows (or columns) containing null values, which is suitable when data loss is negligible. `df.fillna()` imputes missing entries using constants (e.g., 0) or statistical measures (mean, median, mode) or forward/backward filling (`ffill`/`bfill`), avoiding sample size shrinkage.',
            'rubric': {'correctness': 0.40, 'methods_explained': 0.30, 'clarity': 0.30}
        },
        {
            'role_slug': 'data-analyst',
            'skill_slug': 'data-analysis',
            'question_type': 'code-written',
            'difficulty': 'medium',
            'question_text': 'Given a DataFrame `sales_df` with columns `["store_id", "category", "revenue"]`, write Python Pandas code to compute the total revenue and average revenue per store and category, sorted by total revenue in descending order.',
            'expected_concepts': ['groupby(["store_id", "category"])', 'agg({"revenue": ["sum", "mean"]}) or named aggregation', 'sort_values descending'],
            'reference_answer': 'import pandas as pd\n\ndef analyze_sales(sales_df: pd.DataFrame) -> pd.DataFrame:\n    summary = sales_df.groupby(["store_id", "category"], as_index=False).agg(\n        total_revenue=("revenue", "sum"),\n        avg_revenue=("revenue", "mean")\n    ).sort_values(by="total_revenue", ascending=False)\n    return summary',
            'rubric': {'correctness': 0.40, 'aggregation': 0.35, 'sorting': 0.25}
        },
        {
            'role_slug': 'data-analyst',
            'skill_slug': 'data-analysis',
            'question_type': 'technical',
            'difficulty': 'medium',
            'question_text': 'Explain the difference between `df.loc[]` and `df.iloc[]` in Pandas. What happens when boolean masks are passed to each?',
            'expected_concepts': ['df.loc is label-based indexing including endpoints', 'df.iloc is integer-position based indexing excluding endpoints', 'boolean indexing works natively with loc and iloc'],
            'reference_answer': '`df.loc[]` is label-based: it accesses rows and columns by their index and column labels, including the right endpoint when slicing. `df.iloc[]` is integer-position based: it selects elements via 0-indexed integer coordinates and excludes the stop boundary (standard Python slice behavior). Boolean masks can filter rows in `loc`, whereas `iloc` requires positional booleans or array indices.',
            'rubric': {'correctness': 0.40, 'distinction': 0.35, 'clarity': 0.25}
        },
        {
            'role_slug': 'data-analyst',
            'skill_slug': 'data-analysis',
            'question_type': 'technical',
            'difficulty': 'medium',
            'question_text': 'What is the difference between `pd.merge()`, `pd.concat()`, and `DataFrame.join()` in Pandas?',
            'expected_concepts': ['pd.merge performs relational joins (inner, left, right, outer) on columns or indices', 'pd.concat stacks DataFrames along an axis (rows or columns)', 'join is a convenience method combining DataFrames primarily on their index'],
            'reference_answer': '`pd.merge()` performs SQL-style relational database joins on shared keys or columns (inner, left, right, outer). `pd.concat()` stitches together multiple DataFrames along a designated axis (`axis=0` for stacking rows, `axis=1` for pasting columns). `df.join()` is an index-centric helper that merges two DataFrames on their row indices by default.',
            'rubric': {'correctness': 0.40, 'comparison': 0.35, 'clarity': 0.25}
        },
        {
            'role_slug': 'data-analyst',
            'skill_slug': 'data-analysis',
            'question_type': 'code-written',
            'difficulty': 'hard',
            'question_text': 'Write a Pandas function to identify and filter outliers in a numerical column using the Interquartile Range (IQR) method. Explain the 1.5 * IQR multiplier.',
            'expected_concepts': ['calculating Q1 (25th percentile) and Q3 (75th percentile)', 'IQR = Q3 - Q1', 'lower_bound = Q1 - 1.5 * IQR', 'upper_bound = Q3 + 1.5 * IQR', 'filtering rows within bounds'],
            'reference_answer': 'import pandas as pd\n\ndef remove_iqr_outliers(df: pd.DataFrame, column: str) -> pd.DataFrame:\n    q1 = df[column].quantile(0.25)\n    q3 = df[column].quantile(0.75)\n    iqr = q3 - q1\n    lower_bound = q1 - 1.5 * iqr\n    upper_bound = q3 + 1.5 * iqr\n    return df[(df[column] >= lower_bound) & (df[column] <= upper_bound)]\n\nThe 1.5 multiplier captures roughly +/-2.7 standard deviations in a normal distribution, filtering extreme anomalies without over-pruning valid variations.',
            'rubric': {'correctness': 0.40, 'iqr_formula': 0.35, 'explanation': 0.25}
        },
        {
            'role_slug': 'data-analyst',
            'skill_slug': 'data-analysis',
            'question_type': 'technical',
            'difficulty': 'hard',
            'question_text': 'How do vectorization and broadcasting in NumPy/Pandas improve performance compared to Python loops or `df.apply()`?',
            'expected_concepts': ['vectorization executes operations in compiled C/Fortran loops', 'avoids Python interpreter overhead and dynamic type checking per element', 'SIMD processor instructions', 'memory locality in contiguous C arrays'],
            'reference_answer': 'Vectorization replaces slow iterative Python-level loops with compiled, highly optimized C and Fortran routines operating over contiguous arrays in memory. Broadcasting allows arithmetic operations between arrays of differing compatible shapes without memory copying. This bypasses Python interpreter dynamic type-checking overhead per item and allows the hardware to utilize SIMD (Single Instruction Multiple Data) vector CPU registers.',
            'rubric': {'correctness': 0.40, 'performance_depth': 0.35, 'clarity': 0.25}
        },
        {
            'role_slug': 'data-analyst',
            'skill_slug': 'data-analysis',
            'question_type': 'code-written',
            'difficulty': 'hard',
            'question_text': 'Given a time-series DataFrame `df` with columns `["timestamp", "metric_value"]`, write Pandas code to convert the timestamp column, set it as index, and compute a 7-day rolling average and resample daily sums.',
            'expected_concepts': ['pd.to_datetime(df["timestamp"])', 'set_index("timestamp")', 'df.resample("1D").sum()', 'df["metric_value"].rolling(window="7D").mean() or rolling(7).mean()'],
            'reference_answer': 'import pandas as pd\n\ndef process_timeseries(df: pd.DataFrame):\n    df["timestamp"] = pd.to_datetime(df["timestamp"])\n    df = df.set_index("timestamp").sort_index()\n    daily_resampled = df.resample("1D")["metric_value"].sum()\n    rolling_7d = df["metric_value"].rolling("7D").mean()\n    return daily_resampled, rolling_7d',
            'rubric': {'correctness': 0.40, 'timeseries_handling': 0.35, 'code_quality': 0.25}
        },

        # Skill: Behavioral & Situational Communication (HR) (8 questions)
        {
            'role_slug': 'python-developer',
            'skill_slug': 'behavioral-communication',
            'question_type': 'hr',
            'difficulty': 'easy',
            'question_text': 'Tell me about yourself and why you are interested in pursuing this engineering role.',
            'expected_concepts': ['relevant technical background and academic training', 'passion for software development and problem solving', 'alignment with job role responsibilities', 'clear, professional communication structure'],
            'reference_answer': 'The candidate should provide a succinct 2-minute elevator pitch covering their academic background in engineering, practical projects built, core technical proficiencies, and an enthusiastic, concrete explanation of why this specific role matches their career aspirations.',
            'rubric': {'relevance': 0.30, 'structure': 0.30, 'clarity': 0.20, 'motivation': 0.20}
        },
        {
            'role_slug': 'python-developer',
            'skill_slug': 'behavioral-communication',
            'question_type': 'hr',
            'difficulty': 'easy',
            'question_text': 'How do you prioritize your tasks when juggling multiple tight deadlines or competing project deliverables?',
            'expected_concepts': ['Eisenhower matrix or urgency vs importance assessment', 'breaking tasks into milestones', 'proactive communication with stakeholders/team', 're-evaluating priorities when roadblocks occur'],
            'reference_answer': 'A strong answer demonstrates a structured framework for prioritizing work (evaluating urgency vs impact), maintaining clear task tracking, and proactively communicating with teammates and leaders when trade-offs or timeline adjustments are necessary.',
            'rubric': {'structure': 0.35, 'practical_approach': 0.35, 'communication': 0.30}
        },
        {
            'role_slug': 'python-developer',
            'skill_slug': 'behavioral-communication',
            'question_type': 'hr',
            'difficulty': 'medium',
            'question_text': 'Describe a situation where you had a disagreement with a team member over a technical decision or project architecture. How did you resolve it? (Use the STAR framework: Situation, Task, Action, Result).',
            'expected_concepts': ['concrete Situation and Task described', 'constructive Action: active listening, data-driven comparison, prototyping, objective criteria', 'positive Result: consensus reached, project delivered successfully, healthy working relationship preserved'],
            'reference_answer': 'The response must follow the STAR format: detailing the specific disagreement (Situation/Task), actions taken to objectively evaluate alternatives using evidence or benchmarks rather than ego (Action), and the collaborative outcome achieved (Result).',
            'rubric': {'star_structure': 0.35, 'action_and_outcome': 0.35, 'relevance': 0.30}
        },
        {
            'role_slug': 'python-developer',
            'skill_slug': 'behavioral-communication',
            'question_type': 'hr',
            'difficulty': 'medium',
            'question_text': 'Give an example of a project where you made a mistake or encountered a critical failure. What did you learn and how did you prevent it from recurring?',
            'expected_concepts': ['honest acknowledgment of mistake without blaming others', 'immediate mitigation and root-cause analysis', 'preventative measures implemented (automated tests, linting, docs, peer review)', 'long-term growth mindset'],
            'reference_answer': 'Candidates should honestly articulate a mistake, explain the immediate remediation steps taken, conduct an objective root-cause analysis, and demonstrate preventative measures (e.g., CI/CD checks or unit tests) introduced to prevent future regressions.',
            'rubric': {'ownership_accountability': 0.35, 'learning_growth': 0.35, 'structure': 0.30}
        },
        {
            'role_slug': 'python-developer',
            'skill_slug': 'behavioral-communication',
            'question_type': 'hr',
            'difficulty': 'medium',
            'question_text': 'Describe a time when you had to learn a completely new framework, language, or tool on a tight deadline. What was your learning strategy?',
            'expected_concepts': ['structured learning plan (official docs, minimal reproduction, tutorials)', 'building small proof-of-concept prototypes', 'seeking guidance or code reviews when stuck', 'timely delivery of required deliverable'],
            'reference_answer': 'The response should highlight an agile self-directed learning approach: focusing on core fundamentals through official documentation, building proof-of-concept components rapidly, and delivering the objective on schedule.',
            'rubric': {'strategy': 0.35, 'action_outcome': 0.35, 'clarity': 0.30}
        },
        {
            'role_slug': 'python-developer',
            'skill_slug': 'behavioral-communication',
            'question_type': 'hr',
            'difficulty': 'hard',
            'question_text': 'Imagine you discover a critical bug in production on Friday afternoon, right before you are scheduled to log off. How do you respond and handle stakeholder communication?',
            'expected_concepts': ['triage severity and user impact', 'notifying incident lead or team promptly', 'implementing rollback or hotfix if safe', 'transparent communication status updates without panic', 'post-mortem and blameless analysis scheduled'],
            'reference_answer': 'The candidate should display ownership and sound judgment: triaging severity, communicating immediately to team and stakeholders, stabilizing production (via rollback or targeted hotfix), and conducting a blameless post-mortem afterwards.',
            'rubric': {'crisis_management': 0.35, 'communication': 0.35, 'ownership': 0.30}
        },
        {
            'role_slug': 'python-developer',
            'skill_slug': 'behavioral-communication',
            'question_type': 'hr',
            'difficulty': 'hard',
            'question_text': 'How do you handle receiving negative or critical feedback on your code during peer review or performance evaluation?',
            'expected_concepts': ['separating self-worth from the code', 'treating feedback as an opportunity for mastery', 'asking clarifying questions for constructive suggestions', 'implementing changes and expressing appreciation for the review'],
            'reference_answer': 'The candidate should emphasize receptivity to feedback, viewing peer reviews as collective quality enhancement rather than personal criticism, and asking clarifying questions to implement superior technical solutions.',
            'rubric': {'emotional_intelligence': 0.35, 'adaptability': 0.35, 'communication': 0.30}
        },
        {
            'role_slug': 'python-developer',
            'skill_slug': 'behavioral-communication',
            'question_type': 'hr',
            'difficulty': 'hard',
            'question_text': 'Describe a situation where project requirements were ambiguous or kept changing during development. How did you maintain momentum and align with stakeholders?',
            'expected_concepts': ['proactively clarifying ambiguities with stakeholders', 'documenting assumptions and risks', 'adopting incremental iterative deliveries', 'fostering alignment through demos and feedback loops'],
            'reference_answer': 'The candidate should detail how they navigated ambiguity by driving clarification meetings, proposing assumptions in writing, breaking deliverables into rapid verifiable increments, and securing ongoing stakeholder alignment.',
            'rubric': {'initiative_leadership': 0.35, 'adaptability': 0.35, 'communication': 0.30}
        }
    ]

    # Map and insert questions
    added_questions = 0
    for q_data in questions_catalog:
        role_slug = q_data.pop('role_slug')
        skill_slug = q_data.pop('skill_slug')
        role = role_records.get(role_slug)
        skill = skill_records.get(skill_slug)

        if not role or not skill:
            continue

        existing_q = Question.query.filter_by(
            job_role_id=role.id,
            skill_id=skill.id,
            question_text=q_data['question_text']
        ).first()

        if not existing_q:
            new_q = Question(
                job_role_id=role.id,
                skill_id=skill.id,
                is_approved=True,
                is_active=True,
                origin='seed',
                **q_data
            )
            db.session.add(new_q)
            added_questions += 1

    db.session.commit()
    print(f"Question bank seeded: {added_questions} questions added. Total questions in DB: {Question.query.count()}.")
    print("Seed complete successfully.")


if __name__ == '__main__':
    from app import create_app
    app = create_app('development')
    with app.app_context():
        seed_all()
