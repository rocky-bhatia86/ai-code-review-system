"""
AI Code Review Service
Handles OpenAI and Azure OpenAI integration and review logic
"""
from typing import Optional, Dict
from config import settings

# Optional OpenAI imports
try:
    from openai import OpenAI, AzureOpenAI
    
    # Initialize the appropriate client based on configuration
    if settings.is_azure_openai:
        client = AzureOpenAI(
            api_key=settings.AZURE_OPENAI_API_KEY,
            api_version=settings.OPENAI_API_VERSION,
            azure_endpoint=settings.AZURE_OPENAI_ENDPOINT
        ) if settings.AZURE_OPENAI_API_KEY and settings.AZURE_OPENAI_ENDPOINT else None
    else:
        client = OpenAI(
            api_key=settings.OPENAI_API_KEY
        ) if settings.OPENAI_API_KEY else None
        
except ImportError:
    client = None

class ReviewService:
    """Service for handling code reviews using AI"""
    
    def __init__(self):
        self.client = client
        # Use Azure deployment name for Azure OpenAI, regular model for OpenAI
        if settings.is_azure_openai:
            self.model = settings.AZURE_OPENAI_DEPLOYMENT_NAME
        else:
            self.model = settings.OPENAI_MODEL
    
    def review_code(self, code: str, context: str = "general code") -> str:
        """
        Review code using OpenAI/Azure OpenAI or return mock review
        
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
        """Get AI review from OpenAI/Azure OpenAI"""
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
                temperature=0.3
            )
            
            return completion.choices[0].message.content
            
        except Exception as e:
            ai_type = "Azure OpenAI" if settings.is_azure_openai else "OpenAI"
            return f"Error getting {ai_type} review: {str(e)}\n\nFalling back to mock review:\n{self._mock_review(code, context)}"
    
    def _mock_review(self, code: str, context: str) -> str:
        """Generate mock review for testing/offline mode"""
        ai_type = "Azure OpenAI" if settings.is_azure_openai else "OpenAI"
        
        mock_reviews = {
            "general code": f"✅ Mock Review ({ai_type}): Code structure looks good. Consider adding error handling and improving variable names.",
            "Git diff": f"🔍 Mock PR Review ({ai_type}): Changes detected. Ensure they follow project standards and include proper tests.",
            "file upload": f"📁 Mock File Review ({ai_type}): File processed successfully. Check for proper imports and documentation."
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
        Review PR diff with focused technical analysis
        
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
        """Get AI review with line-specific technical comments"""
        try:
            system_prompt = """You are a **Technical Code Review Agent**, an expert in programming languages like Python, Java, and Scala.
            Your job is to perform a **technical code review** focusing on **syntax correctness**, **language best practices**, 
            **readability**, **security**, and **performance**.

            ### **Technical Review Guidelines:**  
            Evaluate the code strictly within the diff against the following:

            #### ✅ **Syntax & Standards:**  
            ✔ Ensure syntax validity and language compatibility  
            ✔ Enforce naming conventions and style consistency  
            ✔ Identify potential syntax issues or incorrect imports  

            #### ✅ **Code Quality & Best Practices:**  
            ✔ Encourage idiomatic language usage  
            ✔ Recommend simplification of verbose logic  
            ✔ Promote clean separation of concerns  
            ✔ Identify missed opportunities for abstraction  

            #### ✅ **Performance & Security:**  
            ✔ Eliminate inefficient operations or resource usage  
            ✔ Detect security vulnerabilities  
            ✔ Recommend optimizations where beneficial  

            Return in this JSON format:
            {
                "overall_review": "Brief technical summary of changes and main concerns",
                "line_comments": [
                    {
                        "file": "filename.py",
                        "line": 45,
                        "severity": "HIGH",
                        "message": "Specific technical issue description and fix recommendation"
                    }
                ]
            }
            
            Focus only on technical aspects. Be concise but actionable."""
            
            user_prompt = f"Review this {context} for technical issues:\n\n{diff_content}"
            
            completion = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.2
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
            ai_type = "Azure OpenAI" if settings.is_azure_openai else "OpenAI"
            return {
                "overall_review": f"Error getting {ai_type} review: {str(e)}",
                "line_comments": []
            }
    
    def _mock_review_diff(self, diff_content: str, context: str) -> Dict:
        """Generate mock technical review for testing"""
        lines = diff_content.count('\n') + 1
        added_lines = diff_content.count('+')
        removed_lines = diff_content.count('-')
        ai_type = "Azure OpenAI" if settings.is_azure_openai else "OpenAI"
        
        # Technical issue detection patterns
        issue_patterns = {
            'eval(': ('HIGH', 'Code injection vulnerability detected'),
            'exec(': ('HIGH', 'Code execution vulnerability detected'), 
            'subprocess.call': ('MEDIUM', 'Potential command injection risk'),
            'password': ('HIGH', 'Hardcoded credentials detected'),
            'api_key': ('HIGH', 'Hardcoded API key detected'),
            'TODO': ('LOW', 'Incomplete implementation'),
            'FIXME': ('MEDIUM', 'Code needs fixing'),
            'print(': ('LOW', 'Debug statement should be removed'),
            'console.log': ('LOW', 'Debug statement should be removed'),
            'def ': ('LOW', 'Consider adding type hints and docstring'),
            'class ': ('LOW', 'Consider adding docstring for new class')
        }
        
        mock_comments = []
        current_file = None
        
        for i, line in enumerate(diff_content.split('\n'), 1):
            # Extract current file being processed
            if line.startswith('diff --git'):
                parts = line.split(' ')
                if len(parts) >= 4:
                    current_file = parts[3][2:] if parts[3].startswith('b/') else parts[3]
            
            # Only check added lines for issues
            if line.startswith('+') and current_file:
                for pattern, (severity, message) in issue_patterns.items():
                    if pattern.lower() in line.lower():
                        mock_comments.append({
                            "file": current_file,
                            "line": i,
                            "severity": severity,
                            "message": message
                        })
        
        return {
            "overall_review": f"Mock Technical Review ({ai_type}): {added_lines} additions, {removed_lines} deletions. Found {len(mock_comments)} technical issues.",
            "line_comments": mock_comments
        }

# Global service instance
review_service = ReviewService() 
