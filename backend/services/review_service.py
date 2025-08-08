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
            system_prompt = """You are a senior software engineer doing a critical code review. 
            Focus on CRITICAL and SEVERE issues only, not minor style issues.
            
            Analyze the git diff and provide:
            1. An overall summary (max 3 sentences)
            2. Line-specific comments for CRITICAL issues only:
               - Security vulnerabilities
               - Logic errors/bugs
               - Performance bottlenecks
               - Breaking changes
               - Missing error handling for critical paths
            
            For line comments, identify the exact line number from the diff and provide:
            - Severity: CRITICAL, HIGH, MEDIUM
            - Issue: Brief description
            - Impact: What could go wrong
            - Fix: Specific solution
            
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
                    }
                ]
            }
            
            Only include HIGH and CRITICAL severity issues. Skip minor style/formatting issues."""
            
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
        
        # Simple critical issue detection
        critical_patterns = {
            'eval(': 'CRITICAL: Code injection vulnerability',
            'subprocess.call': 'HIGH: Potential command injection',
            'password': 'HIGH: Hardcoded credentials detected',
            'api_key': 'HIGH: Hardcoded API key detected',
            'TODO': 'MEDIUM: Unfinished implementation'
        }
        
        mock_comments = []
        for i, line in enumerate(diff_content.split('\n'), 1):
            if line.startswith('+'):  # Only check added lines
                for pattern, issue in critical_patterns.items():
                    if pattern.lower() in line.lower():
                        severity = issue.split(':')[0]
                        mock_comments.append({
                            "line": i,
                            "severity": severity,
                            "issue": issue.split(': ', 1)[1],
                            "impact": f"This could lead to security or stability issues",
                            "fix": f"Review and address the {pattern} usage"
                        })
        
        return {
            "overall_review": f"🔍 Mock Critical Review: {added_lines} additions, {removed_lines} deletions. Found {len(mock_comments)} critical issues that need attention.",
            "line_comments": mock_comments
        }

# Global service instance
review_service = ReviewService() 
