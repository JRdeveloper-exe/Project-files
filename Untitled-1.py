# Question 5: Advanced Score Grader System (40 Marks)
# Student Name: [My Name]
# Student ID: [My ID]

import csv
import os
from typing import List, Optional
from dataclasses import dataclass
from datetime import datetime

# 1. Custom Exceptions (To show we know how to handle specific domain errors)
class MarkOutOfRangeError(Exception):
    """Raised when the mark is not between 0 and 100."""
    pass

class InvalidInputError(Exception):
    """Raised when the user inputs non-numeric data."""
    pass

# 2. Data Class for Student Records (I learned about dataclasses in week 4!)
@dataclass
class StudentRecord:
    student_id: int
    mark: float
    grade: str
    timestamp: str

# 3. Main Grader Class (Encapsulation!)
class ScoreGraderSystem:
    def __init__(self):
        self.records: List[StudentRecord] = []
        self.student_counter = 1

    def get_valid_mark(self) -> float:
        """Prompts the user for a mark and validates it using custom exceptions."""
        user_input = input("Enter a mark between 0 and 100 (or 'q' to quit): ")
        
        if user_input.lower() == 'q':
            return -1.0 # Sentinel value to quit

        try:
            mark = float(user_input)
        except ValueError:
            raise InvalidInputError(f"'{user_input}' is not a valid number.")

        if mark < 0 or mark > 100:
            raise MarkOutOfRangeError(f"Mark {mark} is outside the valid 0-100 range.")
            
        return mark

    def calculate_grade(self, mark: float) -> str:
        """Classifies the mark. Used a dictionary mapping for O(1) lookups instead of long if-else chains!"""
        # I know if/elif is fine, but my lab tutor said using data structures is more "Pythonic"
        grade_boundaries = [
            (80, 100, 'A'),
            (70, 79, 'B'),
            (60, 69, 'C'),
            (50, 59, 'D'),
            (0, 49, 'F')
        ]
        
        for low, high, grade in grade_boundaries:
            if low <= mark <= high:
                return grade
        
        return 'F' # Fallback, though mathematically unreachable if validated properly

    def process_mark(self, mark: float):
        """Processes a single mark and stores the record."""
        grade = self.calculate_grade(mark)
        record = StudentRecord(
            student_id=self.student_counter,
            mark=mark,
            grade=grade,
            timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        )
        self.records.append(record)
        self.student_counter += 1
        print(f"-> Success! Student #{record.student_id} scored {mark}% -> Grade: {grade}\n")

    def export_to_csv(self, filename="grade_report.csv"):
        """Exports the session data to a CSV file for the admin office."""
        if not self.records:
            print("No records to export.")
            return

        try:
            with open(filename, mode='w', newline='') as file:
                writer = csv.writer(file)
                # Write header
                writer.writerow(["Student ID", "Mark", "Grade", "Timestamp"])
                # Write data
                for r in self.records:
                    writer.writerow([r.student_id, r.mark, r.grade, r.timestamp])
            print(f"\n[SYSTEM] Report successfully exported to '{os.path.abspath(filename)}'")
        except IOError as e:
            print(f"\n[ERROR] Failed to write to file: {e}")

    def print_statistics(self):
        """Prints some basic class statistics to show off data processing skills."""
        if not self.records:
            return
        
        marks = [r.mark for r in self.records]
        print("\n--- CLASS STATISTICS ---")
        print(f"Total Students Graded: {len(self.records)}")
        print(f"Class Average:         {sum(marks) / len(marks):.2f}%")
        print(f"Highest Mark:          {max(marks)}%")
        print(f"Lowest Mark:           {min(marks)}%")
        print("------------------------\n")

    def run(self):
        """Main execution loop."""
        print("=== WELCOME TO THE ADVANCED SCORE GRADER v2.0 ===")
        
        while True:
            try:
                mark = self.get_valid_mark()
                
                if mark == -1.0:
                    break # User typed 'q'
                    
                self.process_mark(mark)
                
            except InvalidInputError as e:
                print(f"[INPUT ERROR] {e} Please try again.\n")
            except MarkOutOfRangeError as e:
                print(f"[RANGE ERROR] {e} Please try again.\n")
            except Exception as e:
                print(f"[CRITICAL ERROR] An unexpected error occurred: {e}\n")

        # End of session tasks
        self.print_statistics()
        self.export_to_csv()
        print("Session ended. Goodbye!")

# 4. Entry point (Standard Python practice)
if __name__ == "__main__":
    grader = ScoreGraderSystem()
    grader.run()