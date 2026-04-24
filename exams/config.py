from django.templatetags.static import static


subjects_actual = [
    "Mathematical Logic",
    "Databases",
    "Programming in C",
    "Theory of Computation",
    "Data Structures",
    "Digital Logic",
    "Operating System",
    "Calculus",
    "Computer Networks",
    "Linear Algebra",
    "Algorithms",
    "Graph Theory",
    "CO & Architecture",
    "Verbal Aptitude",
    "Set Theory & Algebra",
    "Probability",
    "Compiler Design",
    "Numerical Methods",
    "Combinatory",
    "Quantitative Aptitude",
    "Object Oriented Programming",
    "IS&Software Engineering",
    "Web Technologies",
    "Analytical Aptitude",
    "Others",
    "Spatial Aptitude",
    "Discrete Mathematics",
    "Programming",
    "Machine Learning",
    "Artificial Intelligence",
    "Programming in Python",
    "Engineering Mathematics",
    "Programming and DS",
    "AI/ML",
    "Exam Queries",
    "Data Mining and Warehousing"
]

subjects = [
    "Programming in C",
    "Mathematical Logic",
    "Discrete Mathematics",
    "Programming",
    "Set Theory & Algebra",
    "Combinatory",
    "Data Structures",
    "Graph Theory",
    "Algorithms",
    "Digital Logic",
    "Theory of Computation",
    "Compiler Design",
    "Linear Algebra",
    "CO & Architecture",
    "Probability",
    "Calculus",
    "Databases",
    "Operating System",
    "Computer Networks",
    "Analytical Aptitude",
    "Quantitative Aptitude",
    "Spatial Aptitude",
    "Verbal Aptitude",
    "Engineering Mathematics",
    "Programming and DS",
    "Programming in Python",
    "AI/ML",
    "Machine Learning",
    "Artificial Intelligence",
    "Others",
    "Exam Queries"
]

# Gate overflow performance analysis pool
# pool_mapping = {
#         "Theory": [
#             "Algorithms", "Theory of Computation", "Digital Logic", 
#             "Mathematical Logic", "Set Theory & Algebra", "Graph Theory", 
#             "Linear Algebra", "Calculus"
#         ],
#         "Intelligence": [
#             "Probability", "Combinatory", "Programming", "DS", "Programming in C"
#         ],
#         "Systems": [
#             "Compiler Design", "CO and Architecture", "Operating System", 
#             "Databases", "Computer Networks"
#         ],
#         "Aptitude": [
#             "Verbal Aptitude", "Quantitative Aptitude", "Analytical Aptitude", "Spatial Aptitude"
#         ],
#         "Others": ["Exam Queries", "Others"]
#     }

pool_mapping = {
    "Math": [
        "Engineering Mathematics",
        "Discrete Mathematics",
        "Linear Algebra",
        "Calculus",
        "Probability",
        "Combinatory",
        "Set Theory & Algebra",
        "Mathematical Logic",
    ],

    "Theory": [
        "Algorithms",
        "Theory of Computation",
        "Digital Logic",
        "Compiler Design",
        "Graph Theory",
    ],

    "Programming": [
        "Programming",
        "Programming in C",
        "Programming in Python",
        "Data Structures",
        "Programming and DS",
        "Artificial Intelligence",
        "Machine Learning",
        "AI/ML",
    ],

    "Systems": [
        "Operating System",
        "Databases",
        "Computer Networks",
        "CO & Architecture",
    ],

    "Aptitude": [
        "Analytical Aptitude",
        "Quantitative Aptitude",
        "Spatial Aptitude",
        "Verbal Aptitude",
    ],

    "Others": [
        "Exam Queries",
        "Others",
    ]
}

q_types_list = ["Multiple Choice", "Multiple Select", "Numerical"]
question_type_short_form = {"Multiple Choice": "MCQ", "Multiple Select": "MSQ", "Numerical": "NAT"}

interface_behavior = {
    "test": 
    {
        "remember_calc_position": True,
        "shuffle_qs": False,
        "allow_early_submit": True,
        "mouse_scrolling":True,
        "question_change_delay":False,
        "global_answer_container": True
    }
    ,
    "simulation": 
    {
        "remember_calc_position": False,
        "shuffle_qs": True,
        "allow_early_submit": False,
        "mouse_scrolling": False,
        "question_change_delay":(300, 50), # means 300ms +- 50ms randomly in this range
        "global_answer_container": False
    }
}

candidate_photo_dir = file_url = static("candidate_profile_images")

ques_status_map = {
    "not_visited": 0,
    "not_answered": 1,
    "answered": 2,
    "marked_for_review": 3,
    "answered_and_marked_for_review": 4
}

ques_status_map_display = [
    "Not Visited", "Not Answered", "Answered", "Marked for review", "Answered and marked for review"
]