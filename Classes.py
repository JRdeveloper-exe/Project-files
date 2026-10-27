class Student:
    
    class_year = 2025
    num_students = 0
    
    def __init__(self, name, age, course):
        self.name = name
        self.age = age
        self.course = course
        self.student = True
        Student.num_students += 1
        
student1 = Student("Jeff", 20, "Data Base")
student2 = Student("Marry", 22, "Mathematics")
student3 = Student("John", 21, "Software")
student4 = Student("Jenna", 23, "Clouding")
student5 = Student("Marcus", 19, "Network")


print(f"Welcome to our number of {Student.num_students} Students, who are: ")
print(" ")
print(f"{student1.name} age {student1.age} with a course of {student1.course}")
print(f"{student2.name} age {student2.age} with a course of {student2.course}")
print(f"{student3.name} age {student3.age} with a course of {student3.course}")
print(f"{student4.name} age {student4.age} with a course of {student4.course}")
print(f"{student5.name} age {student5.age} with a course of {student5.course}")