student_marks = {
    "Alice": 92,
    "Bob": 78,
    "Carol": 85,
}

for student, marks in student_marks.items():
    if marks >= 90:
        print(student + " passed with distinction")
    else:
        print(student + " passed")

