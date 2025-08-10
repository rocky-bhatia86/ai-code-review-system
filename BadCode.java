package com.example.codeissues;

import java.sql.*;
import java.util.*;
import java.io.*;
import java.security.MessageDigest;

/**
 * Java Code Quality Test File
 * Contains various issues for AI code review testing:
 * - Performance issues
 * - Security vulnerabilities  
 * - Code quality problems
 * - Bad practices
 */
public class BadCodeJava {
    
    // SECURITY ISSUE 1: Hardcoded credentials
    private static final String DATABASE_PASSWORD = "admin123";
    private static final String API_KEY = "sk-1234567890abcdef";
    private static final String SECRET_TOKEN = "super_secret_token_123";
    
    // CODE QUALITY ISSUE 1: Public mutable fields
    public List<String> publicData = new ArrayList<>();
    public static int globalCounter = 0;
    
    // PERFORMANCE ISSUE 1: Inefficient data structure choice
    private List<Integer> validIds = Arrays.asList(1, 2, 3, 4, 5, 100, 200, 300, 400, 500);
    
    public BadCodeJava() {
        // PERFORMANCE ISSUE 2: Expensive initialization
        loadAllData(); // Loads everything upfront
    }
    
    private void loadAllData() {
        // PERFORMANCE ISSUE 3: Loading unnecessary data
        for (int i = 0; i < 10000; i++) {
            publicData.add("User" + i + "_" + "x".repeat(1000));
        }
    }
    
    // PERFORMANCE ISSUE 4: Inefficient string concatenation
    public String getUserNames() {
        String result = "";
        for (String user : publicData) {
            result += user + ","; // Creates new String objects each iteration
        }
        return result;
    }
    
    // PERFORMANCE ISSUE 5: Inefficient search algorithm
    public String findUser(int userId) {
        // O(n) linear search when hash map would be O(1)
        for (String user : publicData) {
            if (user.contains("User" + userId + "_")) {
                return user;
            }
        }
        return null;
    }
    
    // PERFORMANCE ISSUE 6: Inefficient membership testing
    public List<Integer> validateUsers(List<Integer> userIds) {
        List<Integer> validUsers = new ArrayList<>();
        for (Integer userId : userIds) {
            if (validIds.contains(userId)) { // O(n) lookup in ArrayList
                validUsers.add(userId);
            }
        }
        return validUsers;
    }
    
    // SECURITY ISSUE 2: SQL Injection vulnerability
    public List<String> getUserData(String userId) throws SQLException {
        Connection conn = DriverManager.getConnection(
            "jdbc:mysql://localhost:3306/users", "root", DATABASE_PASSWORD);
        Statement stmt = conn.createStatement();
        
        // Dangerous: string concatenation in SQL query
        String query = "SELECT * FROM users WHERE id = '" + userId + "'";
        ResultSet rs = stmt.executeQuery(query);
        
        List<String> results = new ArrayList<>();
        while (rs.next()) {
            results.add(rs.getString("name"));
        }
        
        // CODE QUALITY ISSUE 2: Resource leak - not closing connections
        return results;
    }
    
    // SECURITY ISSUE 3: Command injection vulnerability
    public String executeSystemCommand(String filename) throws IOException {
        // Dangerous: unsanitized input in system command
        Process process = Runtime.getRuntime().exec("cat " + filename);
        
        BufferedReader reader = new BufferedReader(
            new InputStreamReader(process.getInputStream()));
        
        StringBuilder result = new StringBuilder();
        String line;
        while ((line = reader.readLine()) != null) {
            result.append(line).append("\n");
        }
        
        return result.toString();
    }
    
    // SECURITY ISSUE 4: Weak password hashing
    public String hashPassword(String password) {
        try {
            MessageDigest md = MessageDigest.getInstance("MD5"); // Weak algorithm
            byte[] hash = md.digest(password.getBytes());
            
            // PERFORMANCE ISSUE 7: Inefficient hex conversion
            String result = "";
            for (byte b : hash) {
                result += String.format("%02x", b); // String concatenation in loop
            }
            return result;
        } catch (Exception e) {
            return password; // SECURITY ISSUE 5: Fallback to plaintext
        }
    }
    
    // PERFORMANCE ISSUE 8: Poor algorithm choice - Bubble Sort
    public int[] sortData(int[] data) {
        int n = data.length;
        // O(n²) when better algorithms exist
        for (int i = 0; i < n - 1; i++) {
            for (int j = 0; j < n - i - 1; j++) {
                if (data[j] > data[j + 1]) {
                    int temp = data[j];
                    data[j] = data[j + 1];
                    data[j + 1] = temp;
                }
            }
        }
        return data;
    }
    
    // PERFORMANCE ISSUE 9: Inefficient recursion without memoization
    public long fibonacci(int n) {
        if (n <= 1) return n;
        // Exponential time complexity
        return fibonacci(n - 1) + fibonacci(n - 2);
    }
    
    // CODE QUALITY ISSUE 3: Method with too many parameters
    public double calculateSomething(double a, double b, double c, double d, 
                                   double e, double f, double g, double h,
                                   boolean flag1, boolean flag2, String mode) {
        
        // CODE QUALITY ISSUE 4: Magic numbers
        if (a > 42.0) {
            double x = b * 3.14159;
            
            // CODE QUALITY ISSUE 5: Deep nesting
            if (flag1) {
                if (flag2) {
                    if (mode.equals("advanced")) {
                        if (c > d) {
                            if (e < f) {
                                return x * 2.5;
                            } else {
                                return x * 1.8;
                            }
                        } else {
                            return x * 1.2;
                        }
                    } else {
                        return x * 0.9;
                    }
                } else {
                    return x * 0.5;
                }
            } else {
                return x * 0.1;
            }
        } else {
            return a + 100; // Another magic number
        }
    }
    
    // CODE QUALITY ISSUE 6: Poor exception handling
    public String riskyOperation() {
        try {
            int result = 10 / 0;
            return String.valueOf(result);
        } catch (Exception e) { // Too broad exception handling
            return ""; // Silent failure
        }
    }
    
    // CODE QUALITY ISSUE 7: Not using enhanced for loop
    public List<String> processItems(List<String> items) {
        List<String> processed = new ArrayList<>();
        for (int i = 0; i < items.size(); i++) {
            String item = items.get(i); // Inefficient for LinkedList
            if (item.length() > 5) {
                processed.add(item.toUpperCase());
            }
        }
        return processed;
    }
    
    // CODE QUALITY ISSUE 8: Inefficient file reading
    public List<String> readFileInefficiently(String filename) throws IOException {
        // Should use try-with-resources
        FileReader fr = new FileReader(filename);
        BufferedReader br = new BufferedReader(fr);
        
        List<String> lines = new ArrayList<>();
        String line;
        while ((line = br.readLine()) != null) {
            lines.add(line);
        }
        
        // CODE QUALITY ISSUE 9: Resource leak - not closing streams
        return lines;
    }
    
    // PERFORMANCE ISSUE 10: Creating unnecessary objects
    public List<String> generateData(int count) {
        List<String> data = new ArrayList<>();
        for (int i = 0; i < count; i++) {
            // Creates new StringBuilder, String objects unnecessarily
            StringBuilder sb = new StringBuilder();
            sb.append("Item_").append(i).append("_").append(new Date().toString());
            data.add(sb.toString());
        }
        return data;
    }
    
    // CODE QUALITY ISSUE 10: Missing proper equals/hashCode
    static class User {
        private String name;
        private int id;
        
        public User(String name, int id) {
            this.name = name;
            this.id = id;
        }
        
        // Missing equals() and hashCode() methods
        // Will cause issues when used in collections
    }
    
    public static void main(String[] args) {
        BadCodeJava example = new BadCodeJava();
        
        // Multiple inefficient operations
        String names = example.getUserNames();
        String user = example.findUser(5000);
        List<Integer> valid = example.validateUsers(Arrays.asList(1, 2, 3, 1000));
        
        System.out.println("Names length: " + names.length());
        System.out.println("Found user: " + (user != null));
        System.out.println("Valid users: " + valid.size());
    }
} 
