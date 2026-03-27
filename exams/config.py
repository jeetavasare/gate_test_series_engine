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

question_type_short_form = {"Multiple Choice": "MCQ", "Multiple Select": "MSQ", "Numerical": "NAT"}