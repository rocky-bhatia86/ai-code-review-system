#!/usr/bin/env python3
"""
Python Code Quality Test File
Contains various issues for AI code review testing:
- Performance issues
- Security vulnerabilities  
- Code quality problems
- Bad practices
"""

import os
import subprocess
import sqlite3

# SECURITY ISSUE 1: Hardcoded credentials
DATABASE_PASSWORD = "admin123"
API_KEY = "sk-1234567890abcdef"
SECRET_TOKEN = "super_secret_token_123"

class UserManager:
    def __init__(self):
        # PERFORMANCE ISSUE 1: Expensive initialization
        self.all_users = self.load_all_users()  # Loads everything upfront
        
    def load_all_users(self):
        """PERFORMANCE ISSUE 2: Loading unnecessary data"""
        # Should paginate or use lazy loading
        return [{"id": i, "name": f"User{i}", "data": "x" * 1000} for i in range(10000)]
    
    def find_user(self, user_id):
        """PERFORMANCE ISSUE 3: Inefficient search in list"""
        # O(n) search, should use dict/hash map
        for user in self.all_users:
            if user["id"] == user_id:
                return user
        return None
    
    def get_user_names(self):
        """PERFORMANCE ISSUE 4: Inefficient string concatenation"""
        result = ""
        for user in self.all_users:
            result += user["name"] + ","  # O(n²) complexity
        return result
    
    def validate_users(self, user_ids):
        """PERFORMANCE ISSUE 5: Inefficient membership testing"""
        valid_ids = [1, 2, 3, 4, 5, 100, 200, 300, 400, 500]  # Should use set
        valid_users = []
        
        for user_id in user_ids:
            if user_id in valid_ids:  # O(n) lookup in list
                valid_users.append(user_id)
        
        return valid_users

def process_user_input(user_data):
    """SECURITY ISSUE 2: Code injection vulnerability"""
    # Dangerous: executing user input as code
    calculation = eval(user_data.get("formula", "0"))
    return calculation

def execute_system_command(filename):
    """SECURITY ISSUE 3: Command injection vulnerability"""
    # Dangerous: unsanitized input in shell command
    command = f"cat {filename}"
    result = subprocess.run(command, shell=True, capture_output=True, text=True)
    return result.stdout

def database_query(user_id):
    """SECURITY ISSUE 4: SQL injection vulnerability"""
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    
    # Dangerous: string formatting in SQL query
    query = f"SELECT * FROM users WHERE id = '{user_id}'"
    cursor.execute(query)
    
    result = cursor.fetchall()
    conn.close()
    return result

def inefficient_algorithm(data):
    """PERFORMANCE ISSUE 6: Poor algorithm choice - Bubble Sort"""
    n = len(data)
    # O(n²) when better algorithms exist
    for i in range(n):
        for j in range(0, n - i - 1):
            if data[j] > data[j + 1]:
                data[j], data[j + 1] = data[j + 1], data[j]
    return data

def recursive_fibonacci(n):
    """PERFORMANCE ISSUE 7: Inefficient recursion without memoization"""
    if n <= 1:
        return n
    # Exponential time complexity - recalculates same values
    return recursive_fibonacci(n-1) + recursive_fibonacci(n-2)

def process_file_inefficiently(filename):
    """PERFORMANCE ISSUE 8: Loading entire file into memory"""
    # Should process line by line for large files
    with open(filename, 'r') as f:
        all_lines = f.readlines()
    
    processed = []
    for line in all_lines:
        if 'important' in line:
            processed.append(line.strip())
    
    return processed

# CODE QUALITY ISSUE 1: Poor function design
def doEverything(a, b, c, d, e, f, g, h):  # Too many parameters
    """CODE QUALITY ISSUE 2: Missing docstring details"""
    # CODE QUALITY ISSUE 3: Magic numbers
    if a > 42:
        x = b * 3.14159
    else:
        x = c + 100
    
    # CODE QUALITY ISSUE 4: Deep nesting
    if d:
        if e:
            if f:
                if g:
                    if h:
                        return x * 2
                    else:
                        return x * 3
                else:
                    return x * 4
            else:
                return x * 5
        else:
            return x * 6
    else:
        return x * 7

# CODE QUALITY ISSUE 5: Global variables
global_counter = 0
global_data = {}

def increment_global():
    """CODE QUALITY ISSUE 6: Modifying global state"""
    global global_counter
    global_counter += 1
    return global_counter

# CODE QUALITY ISSUE 7: Poor exception handling
def risky_operation():
    try:
        result = 10 / 0
        return result
    except:  # Too broad exception handling
        pass  # Silent failure

# CODE QUALITY ISSUE 8: Mutable default arguments
def add_item(item, items=[]):
    items.append(item)
    return items

# CODE QUALITY ISSUE 9: Not using comprehensions
def get_even_numbers(numbers):
    result = []
    for num in numbers:
        if num % 2 == 0:
            result.append(num)
    return result

# CODE QUALITY ISSUE 10: Not using enumerate
def find_index(items, target):
    for i in range(len(items)):
        if items[i] == target:
            return i
    return -1

# SECURITY ISSUE 5: Hardcoded secrets in environment
def setup_environment():
    os.environ["SECRET_KEY"] = "hardcoded_secret_123"
    os.environ["DB_PASSWORD"] = DATABASE_PASSWORD

if __name__ == "__main__":
    # PERFORMANCE ISSUE 9: Inefficient data processing
    manager = UserManager()
    
    # Multiple inefficient operations
    user = manager.find_user(5000)
    names = manager.get_user_names()
    valid = manager.validate_users(range(1000))
    
    # Security risks
    user_input = {"formula": "2 + 2"}
    calc_result = process_user_input(user_input)
    
    print(f"Found user: {user}")
    print(f"Calculation: {calc_result}") 
