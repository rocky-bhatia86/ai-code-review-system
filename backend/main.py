"""
AI Code Review System - Main FastAPI Application
"""
from fastapi import FastAPI, HTTPException, Request, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
import json
from typing import Optional

# Import our modules
from models import (
    CodeRequest, ReviewResponse, FileUploadRequest, 
    GitHubWebhookEvent, PRReviewRequest
)
from services.review_service import review_service
from services.git_service import github_service
from config import settings

# Create FastAPI app
app = FastAPI(
    title="AI Code Review System",
    description="Automated code review using AI with GitHub integration",
    version="1.0.0"
)

# Add CORS middleware for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # React dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    """Health check endpoint"""
    return {
        "message": "AI Code Review System is running!",
        "openai_enabled": settings.openai_enabled,
        "github_enabled": settings.github_enabled
    }

@app.post("/review", response_model=ReviewResponse)
def review_code(request: CodeRequest):
    """
    Review code pasted by user
    """
    try:
        review = review_service.review_code(request.code, "general code")
        return ReviewResponse(review=review)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Review failed: {str(e)}")

@app.post("/review/file", response_model=ReviewResponse)
async def review_uploaded_file(file: UploadFile = File(...)):
    """
    Review code from uploaded file
    """
    try:
        # Read file content
        content = await file.read()
        code = content.decode('utf-8')
        
        # Get file extension for context
        file_ext = file.filename.split('.')[-1] if '.' in file.filename else "unknown"
        context = f"uploaded {file_ext} file"
        
        review = review_service.review_code(code, context)
        
        return ReviewResponse(
            review=f"📁 **File: {file.filename}**\n\n{review}"
        )
        
    except UnicodeDecodeError:
        raise HTTPException(status_code=400, detail="File must be a text file")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"File review failed: {str(e)}")

@app.post("/webhook/github")
async def github_webhook(request: Request):
    """  
    Handle GitHub webhook events for pull requests
    """
    try:
        # Get raw payload for signature verification
        payload_body = await request.body()
        signature = request.headers.get("X-Hub-Signature-256", "")
        
        # Verify webhook signature
        if not github_service.verify_webhook_signature(payload_body, signature):
            raise HTTPException(status_code=401, detail="Invalid webhook signature")
        
        # Parse JSON payload
        webhook_data = json.loads(payload_body.decode())
        
        # Parse PR info
        pr_info = github_service.parse_webhook_pr(webhook_data)
        if not pr_info:
            return {"message": "Not a pull request event"}
        
        # Only process opened or updated PRs
        if pr_info["action"] not in ["opened", "synchronize"]:
            return {"message": f"Ignored action: {pr_info['action']}"}
        
        # Get PR diff
        diff_content = github_service.get_pr_diff(
            pr_info["repo_owner"], 
            pr_info["repo_name"], 
            pr_info["pr_number"]
        )
        
        if not diff_content:
            return {"message": "Could not fetch PR diff"}
        
        # Review the diff with line-specific comments
        review_result = review_service.review_pr_diff(diff_content, "Git diff")
        
        # Parse diff to get proper file paths and line numbers for inline comments
        mapped_comments = review_service.parse_diff_for_inline_comments(
            diff_content, 
            review_result.get("line_comments", [])
        )
        
        # Prepare GitHub inline comments (combine multiple issues per line)
        github_comments = []
        if mapped_comments:
            from models import ReviewComment
            from collections import defaultdict
            
            # Group comments by file and line
            comments_by_location = defaultdict(list)
            for comment in mapped_comments:
                key = (comment['file_path'], comment['actual_line'])
                comments_by_location[key].append(comment)
            
            # Create one comment per location
            for (file_path, line_num), comments in comments_by_location.items():
                if len(comments) == 1:
                    # Single issue
                    comment = comments[0]
                    body = f"**🚨 {comment['severity']}**: {comment['issue']}\n\n**Impact**: {comment['impact']}\n\n**Fix**: {comment['fix']}"
                else:
                    # Multiple issues on same line
                    body = f"**🚨 Multiple Issues Found ({len(comments)} issues):**\n\n"
                    for i, comment in enumerate(comments, 1):
                        body += f"**{i}. {comment['severity']}**: {comment['issue']}\n"
                        body += f"   - **Impact**: {comment['impact']}\n"
                        body += f"   - **Fix**: {comment['fix']}\n\n"
                
                github_comments.append(ReviewComment(
                    body=body,
                    path=file_path,
                    position=comments[0]['diff_position']  # Use diff position instead of line number
                ))
        
        # Create overall review comment
        overall_comment = f"""## 🤖 AI Code Review - Critical Issues Only
        
**Pull Request:** {pr_info['pr_title']}
**Author:** @{pr_info['author']}

{review_result['overall_review']}

**Critical Issues Found:** {len(mapped_comments)} inline comments posted

---
*Automated critical review by AI Code Review System*
        """
        
        # Post PR review with inline comments
        success = github_service.post_pr_review(
            pr_info["repo_owner"],
            pr_info["repo_name"], 
            pr_info["pr_number"],
            overall_comment,
            github_comments
        )
        
        if success:
            return {"message": "Review posted successfully"}
        else:
            return {"message": "Failed to post review"}
            
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON payload")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Webhook processing failed: {str(e)}")

@app.post("/review/pr", response_model=ReviewResponse)
def review_pr_manually(request: PRReviewRequest):
    """
    Manually review a pull request by URL
    For testing and manual triggers
    """
    try:
        # Parse GitHub URL (PR, branch, or compare)
        # Examples: 
        # - https://github.com/owner/repo/pull/123
        # - https://github.com/owner/repo/tree/branch-name
        # - https://github.com/owner/repo/compare/main...branch
        url_parts = request.pr_url.replace("https://github.com/", "").split("/")
        
        if len(url_parts) < 4:
            raise HTTPException(status_code=400, detail="Invalid GitHub URL format")
        
        repo_owner = url_parts[0]
        repo_name = url_parts[1]
        url_type = url_parts[2]  # "pull", "tree", or "compare"
        
        if url_type == "pull":
            pr_number = int(url_parts[3])
        elif url_type == "tree":
            # For branch URLs, we'll fetch the branch content directly
            branch_name = url_parts[3]
            pr_number = None
        else:
            raise HTTPException(status_code=400, detail="Unsupported GitHub URL type. Use /pull/ or /tree/ URLs")
        
        # Get content to review
        if request.diff_content:
            content_to_review = request.diff_content
            context = "provided diff"
        elif url_type == "pull" and pr_number:
            content_to_review = github_service.get_pr_diff(repo_owner, repo_name, pr_number)
            context = "Pull Request diff"
            if not content_to_review:
                raise HTTPException(status_code=404, detail="Could not fetch PR diff")
        elif url_type == "tree":
            # For branch URLs, fetch main files from the branch
            import requests
            try:
                # Get the main application file (common names)
                main_files = ['app.py', 'main.py', 'index.js', 'src/App.js', 'README.md']
                content_to_review = ""
                
                for filename in main_files:
                    file_url = f"https://raw.githubusercontent.com/{repo_owner}/{repo_name}/{branch_name}/{filename}"
                    response = requests.get(file_url)
                    if response.status_code == 200:
                        content_to_review += f"# File: {filename}\n{response.text}\n\n"
                
                if not content_to_review:
                    raise HTTPException(status_code=404, detail="Could not fetch any files from the branch")
                    
                context = f"branch '{branch_name}' files"
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Error fetching branch content: {str(e)}")
        else:
            raise HTTPException(status_code=400, detail="No content to review")
        
        # Review the content with critical focus
        if url_type == "pull" and pr_number:
            # Use diff-specific review for PRs
            review_result = review_service.review_pr_diff(content_to_review, context)
            
            # Format line comments for display
            line_comments_text = ""
            if review_result.get("line_comments"):
                line_comments_text = "\n\n## 🚨 Critical Issues:\n"
                for i, comment in enumerate(review_result["line_comments"], 1):
                    line_comments_text += f"\n**{i}. Line {comment['line']} - {comment['severity']}**\n"
                    line_comments_text += f"- **Issue**: {comment['issue']}\n"
                    line_comments_text += f"- **Impact**: {comment['impact']}\n"
                    line_comments_text += f"- **Fix**: {comment['fix']}\n"
            
            review_text = f"{review_result['overall_review']}{line_comments_text}"
        else:
            # Use regular review for branch/file content
            review_text = review_service.review_code(content_to_review, context)
        
        return ReviewResponse(
            review=f"🔍 **Critical Review for:** {request.pr_url}\n\n{review_text}"
        )
        
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid PR number in URL")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"PR review failed: {str(e)}")

# For development - show configuration status
@app.get("/status")
def get_status():
    """Get system status and configuration"""
    return {
        "openai_configured": settings.openai_enabled,
        "github_configured": settings.github_enabled,
        "openai_model": settings.OPENAI_MODEL,
        "server": f"{settings.HOST}:{settings.PORT}"
    }
