"""
AI Code Review Service
Handles OpenAI integration and review logic
"""
from typing import Optional, Dict
from config import settings

# Optional OpenAI import
try:
    from openai import OpenAI
    client = OpenAI(api_key=settings.OPENAI_API_KEY) if settings.OPENAI_API_KEY else None
except ImportError:
    client = None

class ReviewService:
    """Service for handling code reviews using AI"""
    
    def __init__(self):
        self.client = client
        self.model = settings.OPENAI_MODEL
    
    def review_code(self, code: str, context: str = "general code") -> str:
        """
        Review code using OpenAI or return mock review
        
        Args:
            code: The code to review
            context: Context about the code (e.g., "Python function", "Git diff")
            
        Returns:
            Review feedback as string
        """
        if not code.strip():
            return "No code provided for review."
        
        if self.client and settings.openai_enabled:
            return self._ai_review(code, context)
        else:
            return self._mock_review(code, context)
    
    def _ai_review(self, code: str, context: str) -> str:
        """Get AI review from OpenAI"""
        try:
            system_prompt = """You are a senior software engineer reviewing code. 
            Provide constructive feedback focusing on:
            - Code quality and best practices
            - Potential bugs or security issues  
            - Performance improvements
            - Readability and maintainability
            Keep feedback clear and actionable."""
            
            user_prompt = f"Review this {context}:\n\n{code}"
            
            completion = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.3  # Lower temperature for more consistent reviews
            )
            
            return completion.choices[0].message.content
            
        except Exception as e:
            return f"Error getting AI review: {str(e)}\n\nFalling back to mock review:\n{self._mock_review(code, context)}"
    
    def _mock_review(self, code: str, context: str) -> str:
        """Generate mock review for testing/offline mode"""
        mock_reviews = {
            "general code": "✅ Mock Review: Code structure looks good. Consider adding error handling and improving variable names.",
            "Git diff": "🔍 Mock PR Review: Changes detected. Ensure they follow project standards and include proper tests.",
            "file upload": "📁 Mock File Review: File processed successfully. Check for proper imports and documentation."
        }
        
        base_review = mock_reviews.get(context, mock_reviews["general code"])
        
        # Add some basic analysis
        lines = code.count('\n') + 1
        has_functions = 'def ' in code or 'function ' in code
        has_classes = 'class ' in code
        
        analysis = f"\n\n📊 Basic Analysis:\n- Lines of code: {lines}\n- Contains functions: {has_functions}\n- Contains classes: {has_classes}"
        
        return base_review + analysis

    def review_pr_diff(self, diff_content: str, context: str = "PR diff") -> Dict:
        """
        Review PR diff and generate line-specific critical comments
        
        Args:
            diff_content: Git diff content
            context: Context about the PR
            
        Returns:
            Dictionary with overall review and line-specific comments
        """
        if not diff_content.strip():
            return {
                "overall_review": "No changes detected in the PR.",
                "line_comments": []
            }
        
        if self.client and settings.openai_enabled:
            return self._ai_review_diff(diff_content, context)
        else:
            return self._mock_review_diff(diff_content, context)
    
    def _ai_review_diff(self, diff_content: str, context: str) -> Dict:
        """Get AI review with line-specific critical comments"""
        try:
            system_prompt = """You are a senior software engineer doing a comprehensive code review. 
            Provide thorough feedback on all important aspects of the code changes.
            
            Analyze the git diff and provide:
            1. An overall summary (max 3 sentences)
            2. Line-specific comments for ALL significant issues:
               - 🚨 CRITICAL: Security vulnerabilities, data corruption risks
               - ⚠️ HIGH: Logic errors, performance bottlenecks, breaking changes
               - 📝 MEDIUM: Code quality, best practices, maintainability
               - 💡 LOW: Optimizations, suggestions, minor improvements
            
            For line comments, identify the exact line number from the diff and provide:
            - Severity: CRITICAL, HIGH, MEDIUM, LOW
            - Issue: Brief description
            - Impact: What could go wrong or be improved
            - Fix: Specific solution or suggestion
            
            Return in this JSON format:
            {
                "overall_review": "Brief summary of changes and main concerns",
                "line_comments": [
                    {
                        "line": 45,
                        "severity": "CRITICAL",
                        "issue": "SQL injection vulnerability",
                        "impact": "Database could be compromised",
                        "fix": "Use parameterized queries"
                    },
                    {
                        "line": 52,
                        "severity": "MEDIUM",
                        "issue": "Missing docstring",
                        "impact": "Reduces code maintainability and understanding",
                        "fix": "Add descriptive docstring explaining function purpose"
                    }
                ]
            }
            
            Include ALL severity levels. Be thorough but concise. Focus on actionable feedback."""
            
            user_prompt = f"Review this {context} and focus on critical issues:\n\n{diff_content}"
            
            completion = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.2  # Lower temperature for consistent critical analysis
            )
            
            # Parse AI response as JSON
            import json
            try:
                result = json.loads(completion.choices[0].message.content)
                return result
            except json.JSONDecodeError:
                # Fallback if AI doesn't return proper JSON
                return {
                    "overall_review": completion.choices[0].message.content,
                    "line_comments": []
                }
            
        except Exception as e:
            return {
                "overall_review": f"Error getting AI review: {str(e)}",
                "line_comments": []
            }
    
    def _mock_review_diff(self, diff_content: str, context: str) -> Dict:
        """Generate mock critical review for testing"""
        lines = diff_content.count('\n') + 1
        added_lines = diff_content.count('+')
        removed_lines = diff_content.count('-')
        
        # Comprehensive issue detection patterns
        issue_patterns = {
            'eval(': 'CRITICAL: Code injection vulnerability',
            'exec(': 'CRITICAL: Code execution vulnerability', 
            'subprocess.call': 'HIGH: Potential command injection',
            'password': 'HIGH: Hardcoded credentials detected',
            'api_key': 'HIGH: Hardcoded API key detected',
            'secret': 'HIGH: Hardcoded secret detected',
            'TODO': 'MEDIUM: Unfinished implementation',
            'FIXME': 'MEDIUM: Code needs fixing',
            'HACK': 'MEDIUM: Non-standard implementation',
            'def ': 'LOW: New function added - consider adding docstring',
            'class ': 'LOW: New class added - consider adding docstring',
            'import ': 'LOW: New import - verify it\'s necessary',
            'print(': 'LOW: Debug print statement - consider removing',
            'console.log': 'LOW: Debug log statement - consider removing'
        }
        
        mock_comments = []
        for i, line in enumerate(diff_content.split('\n'), 1):
            if line.startswith('+'):  # Only check added lines
                for pattern, issue in issue_patterns.items():
                    if pattern.lower() in line.lower():
                        severity = issue.split(':')[0]
                        issue_desc = issue.split(': ', 1)[1]
                        
                        # Customize impact and fix based on severity
                        if severity == 'CRITICAL':
                            impact = "This could lead to severe security vulnerabilities"
                            fix = f"Immediately review and secure the {pattern.strip()} usage"
                        elif severity == 'HIGH':
                            impact = "This could lead to security or stability issues"
                            fix = f"Review and address the {pattern.strip()} usage"
                        elif severity == 'MEDIUM':
                            impact = "This affects code quality and maintainability"
                            fix = f"Consider improving the {pattern.strip()} implementation"
                        else:  # LOW
                            impact = "This could improve code quality"
                            fix = f"Consider optimizing the {pattern.strip()} usage"
                        
                        mock_comments.append({
                            "line": i,
                            "severity": severity,
                            "issue": issue_desc,
                            "impact": impact,
                            "fix": fix
                        })
        
        return {
            "overall_review": f"🔍 Mock Critical Review: {added_lines} additions, {removed_lines} deletions. Found {len(mock_comments)} critical issues that need attention.",
            "line_comments": mock_comments
        }

    def parse_diff_for_inline_comments(self, diff_content: str, line_comments: list) -> list:
        """
        Map AI diff line numbers to GitHub diff positions
        
        Args:
            diff_content: Raw git diff content  
            line_comments: List of comments with diff line numbers from AI
            
        Returns:
            List of comments with proper file paths and GitHub diff positions
        """
        if not diff_content or not line_comments:
            return []
        
        print(f"🔍 DEBUG: Mapping {len(line_comments)} AI diff lines to GitHub positions")
        
        # Build mapping from diff_line_number -> (file_path, github_position)
        diff_line_to_position = {}  # diff_line_num -> (file_path, github_position)
        current_file = None
        github_position = 0  # GitHub position within current file (continuous across hunks)
        
        diff_lines = diff_content.splitlines()
        for diff_line_num, line in enumerate(diff_lines, 1):
            if line.startswith('diff --git '):
                # Extract file path correctly: use b/ side (new file)
                parts = line.split(' ')
                if len(parts) >= 4:
                    # parts[3] is 'b/filename', strip the 'b/' prefix
                    b_path = parts[3]
                    current_file = b_path[2:] if b_path.startswith('b/') else b_path
                    print(f"📁 DEBUG: Found file: {current_file}")
                # Reset for new file
                github_position = 0
                
            elif line.startswith('@@'):
                # Start of hunk - DON'T reset github_position (continuous across hunks)
                print(f"📍 DEBUG: Hunk header at diff line {diff_line_num}")
                
            elif current_file is not None:
                # Process hunk content lines
                if line.startswith('+') and not line.startswith('+++'):
                    # Added line - this can be commented on
                    diff_line_to_position[diff_line_num] = (current_file, github_position)
                    print(f"🎯 DEBUG: Diff line {diff_line_num} (+) → {current_file}:pos{github_position}")
                    github_position += 1
                    
                elif line.startswith('-') and not line.startswith('---'):
                    # Deleted line - counts for position but not commentable on right side
                    github_position += 1
                    
                elif line and not line.startswith('\\'):
                    # Context line - can be commented on
                    diff_line_to_position[diff_line_num] = (current_file, github_position)
                    print(f"🎯 DEBUG: Diff line {diff_line_num} (ctx) → {current_file}:pos{github_position}")
                    github_position += 1
        
        print(f"🗺️  DEBUG: Created {len(diff_line_to_position)} diff line→position mappings")
        
        # Map AI comments (diff line numbers) to GitHub positions
        mapped_comments = []
        for i, comment in enumerate(line_comments):
            ai_diff_line = comment['line']  # This is a diff line number
            print(f"🔍 DEBUG: Mapping AI comment {i+1}: diff line {ai_diff_line}")
            
            # Direct mapping from diff line to GitHub position
            if ai_diff_line in diff_line_to_position:
                file_path, github_pos = diff_line_to_position[ai_diff_line]
                mapped_comments.append({
                    **comment,
                    'file_path': file_path,
                    'diff_position': github_pos
                })
                print(f"✅ DEBUG: Mapped diff line {ai_diff_line} → {file_path}:pos{github_pos}")
            else:
                # Fallback: find closest commentable line
                best_match = None
                best_distance = float('inf')
                
                for diff_line, (file_path, github_pos) in diff_line_to_position.items():
                    distance = abs(diff_line - ai_diff_line)
                    if distance <= 3 and distance < best_distance:
                        best_match = (file_path, github_pos)
                        best_distance = distance
                
                if best_match:
                    file_path, github_pos = best_match
                    mapped_comments.append({
                        **comment,
                        'file_path': file_path,
                        'diff_position': github_pos
                    })
                    print(f"🎯 DEBUG: Fuzzy match diff line {ai_diff_line} → {file_path}:pos{github_pos} (±{best_distance})")
                else:
                    print(f"❌ DEBUG: No mapping found for diff line {ai_diff_line}")
        
        print(f"✅ DEBUG: Successfully mapped {len(mapped_comments)}/{len(line_comments)} comments")
        return mapped_comments

# Global service instance
review_service = ReviewService() 
