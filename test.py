"""
Performance Issues Test File
This file contains various performance problems for testing AI code review
"""

import time
import requests

def inefficient_loop():
    """Multiple performance issues in loops"""
    
    # Performance Issue 1: Inefficient string concatenation
    result = ""
    for i in range(10000):
        result += str(i) + ","  # Should use list and join()
    
    # Performance Issue 2: Unnecessary list creation in loop
    numbers = []
    for i in range(1000):
        numbers.append(i)
        if i in numbers:  # O(n) lookup in list
            print(f"Found {i}")
    
    return result

def database_queries():
    """Database query performance issues"""
    
    users = get_all_users()
    
    # Performance Issue 3: N+1 query problem
    user_profiles = []
    for user in users:
        profile = get_user_profile(user.id)  # Should batch these queries
        user_profiles.append(profile)
    
    # Performance Issue 4: Loading unnecessary data
    all_data = load_entire_table()  # Should paginate or filter
    filtered_data = [item for item in all_data if item.active]
    
    return user_profiles, filtered_data

def inefficient_data_structures():
    """Poor choice of data structures"""
    
    # Performance Issue 5: Using list for membership testing
    valid_ids = [1, 2, 3, 4, 5, 100, 200, 300, 400, 500]  # Should use set
    
    user_ids = range(1000)
    valid_users = []
    
    for user_id in user_ids:
        if user_id in valid_ids:  # O(n) lookup, should be O(1) with set
            valid_users.append(user_id)
    
    # Performance Issue 6: Unnecessary sorting in loop
    data = list(range(1000))
    results = []
    
    for i in range(100):
        data.sort()  # Sorting same data repeatedly
        results.append(data[i])
    
    return valid_users, results

def memory_inefficient():
    """Memory usage issues"""
    
    # Performance Issue 7: Loading large data into memory unnecessarily
    with open('large_file.txt', 'r') as f:
        all_lines = f.readlines()  # Should process line by line
    
    processed = []
    for line in all_lines:
        if 'important' in line:
            processed.append(line.strip())
    
    # Performance Issue 8: Creating unnecessary copies
    original_data = list(range(100000))
    copied_data = original_data.copy()  # Unnecessary copy
    modified_data = copied_data.copy()  # Another unnecessary copy
    
    return processed, modified_data

def api_performance_issues():
    """API call performance problems"""
    
    urls = [
        'https://api.example.com/user/1',
        'https://api.example.com/user/2',
        'https://api.example.com/user/3',
        'https://api.example.com/user/4',
        'https://api.example.com/user/5'
    ]
    
    # Performance Issue 9: Sequential API calls instead of parallel
    responses = []
    for url in urls:
        response = requests.get(url)  # Should use async or threading
        responses.append(response.json())
        time.sleep(0.1)  # Unnecessary delay
    
    return responses

def inefficient_algorithms():
    """Algorithmic performance issues"""
    
    # Performance Issue 10: Inefficient sorting algorithm (bubble sort)
    def bubble_sort(arr):
        n = len(arr)
        for i in range(n):
            for j in range(0, n - i - 1):
                if arr[j] > arr[j + 1]:
                    arr[j], arr[j + 1] = arr[j + 1], arr[j]
        return arr
    
    # Performance Issue 11: Inefficient search in unsorted data
    def find_item(items, target):
        for i, item in enumerate(items):  # Should sort first or use binary search
            if item == target:
                return i
        return -1
    
    # Performance Issue 12: Recursive function without memoization
    def fibonacci(n):
        if n <= 1:
            return n
        return fibonacci(n-1) + fibonacci(n-2)  # Exponential time complexity
    
    data = list(range(1000, 0, -1))
    sorted_data = bubble_sort(data)
    
    result = find_item(sorted_data, 500)
    fib_result = fibonacci(30)  # Very slow
    
    return result, fib_result

class InefficientClass:
    """Class with performance issues"""
    
    def __init__(self):
        # Performance Issue 13: Expensive initialization
        self.data = self._load_expensive_data()
        self.cache = {}  # Good: has cache
    
    def _load_expensive_data(self):
        """Simulate expensive data loading"""
        time.sleep(1)  # Performance Issue 14: Blocking operation in __init__
        return list(range(100000))
    
    def get_item(self, index):
        """Get item with caching issues"""
        
        # Performance Issue 15: Not using available cache effectively
        if index in self.cache:
            return self.cache[index]
        
        # Expensive calculation that could be cached
        result = sum(self.data[:index])  # O(n) operation
        self.cache[index] = result
        
        return result
    
    def process_all(self):
        """Process all data inefficiently"""
        
        # Performance Issue 16: Processing data multiple times
        filtered = [x for x in self.data if x % 2 == 0]
        squared = [x * x for x in filtered]
        final = [x for x in squared if x > 100]
        
        # Should combine into single comprehension:
        # final = [x * x for x in self.data if x % 2 == 0 and x * x > 100]
        
        return final

# Helper functions (simulate database calls)
def get_all_users():
    return [type('User', (), {'id': i}) for i in range(100)]

def get_user_profile(user_id):
    time.sleep(0.01)  # Simulate database query
    return {'id': user_id, 'name': f'User {user_id}'}

def load_entire_table():
    return [type('Record', (), {'id': i, 'active': i % 3 == 0}) for i in range(10000)] 
