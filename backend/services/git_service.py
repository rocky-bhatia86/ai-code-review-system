"""
GitHub Integration Service
Handles GitHub API calls, webhook processing, and PR reviews
"""
import requests
import json
import hashlib
import hmac
from typing import Dict, List, Optional
from config import settings
from models import ReviewComment

class GitHubService:
    """Service for GitHub API integration"""
    
    def __init__(self):
        self.token = settings.GITHUB_TOKEN
        self.webhook_secret = settings.GITHUB_WEBHOOK_SECRET
        self.base_url = "https://api.github.com"
        
        # Headers for GitHub API requests
        self.headers = {
            "Authorization": f"token {self.token}" if self.token else "",
            "Accept": "application/vnd.github.v3+json",
            "Content-Type": "application/json"
        }
    
    def verify_webhook_signature(self, payload_body: bytes, signature_header: str) -> bool:
        """
        Verify GitHub webhook signature for security
        
        Args:
            payload_body: Raw webhook payload
            signature_header: X-Hub-Signature-256 header from GitHub
            
        Returns:
            True if signature is valid
        """
        if not self.webhook_secret:
            return True  # Skip verification if no secret configured
        
        expected_signature = "sha256=" + hmac.new(
            self.webhook_secret.encode(),
            payload_body,
            hashlib.sha256
        ).hexdigest()
        
        return hmac.compare_digest(expected_signature, signature_header)
    
    def get_pr_diff(self, repo_owner: str, repo_name: str, pr_number: int) -> Optional[str]:
        """
        Get the diff content of a pull request
        
        Args:
            repo_owner: GitHub repository owner
            repo_name: GitHub repository name  
            pr_number: Pull request number
            
        Returns:
            Diff content as string or None if error
        """
        if not self.token:
            return None
            
        url = f"{self.base_url}/repos/{repo_owner}/{repo_name}/pulls/{pr_number}"
        
        try:
            # Get PR diff in unified format
            headers = self.headers.copy()
            headers["Accept"] = "application/vnd.github.v3.diff"
            
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            
            return response.text
            
        except requests.RequestException as e:
            print(f"Error fetching PR diff: {e}")
            return None
    
    def get_pr_files(self, repo_owner: str, repo_name: str, pr_number: int) -> List[Dict]:
        """
        Get list of files changed in a pull request
        
        Returns:
            List of file objects with filename, status, changes, etc.
        """
        if not self.token:
            return []
            
        url = f"{self.base_url}/repos/{repo_owner}/{repo_name}/pulls/{pr_number}/files"
        
        try:
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            
            return response.json()
            
        except requests.RequestException as e:
            print(f"Error fetching PR files: {e}")
            return []
    
    def post_pr_comment(self, repo_owner: str, repo_name: str, pr_number: int, 
                       comment_body: str) -> bool:
        """
        Post a general comment to a pull request
        
        Args:
            repo_owner: Repository owner
            repo_name: Repository name
            pr_number: PR number
            comment_body: Comment text
            
        Returns:
            True if successful
        """
        if not self.token:
            return False
            
        url = f"{self.base_url}/repos/{repo_owner}/{repo_name}/issues/{pr_number}/comments"
        
        data = {"body": comment_body}
        
        try:
            response = requests.post(url, headers=self.headers, json=data)
            response.raise_for_status()
            return True
            
        except requests.RequestException as e:
            print(f"Error posting PR comment: {e}")
            return False
    
    def post_pr_review(self, repo_owner: str, repo_name: str, pr_number: int,
                      review_body: str, comments: List[ReviewComment] = None) -> bool:
        """
        Post a review with inline comments to a pull request
        
        Args:
            repo_owner: Repository owner
            repo_name: Repository name  
            pr_number: PR number
            review_body: Overall review summary
            comments: List of inline comments
            
        Returns:
            True if successful
        """
        if not self.token:
            return False
            
        url = f"{self.base_url}/repos/{repo_owner}/{repo_name}/pulls/{pr_number}/reviews"
        
        data = {
            "body": review_body,
            "event": "COMMENT",  # COMMENT, APPROVE, or REQUEST_CHANGES
            "comments": [comment.dict() for comment in (comments or [])]
        }
        
        # Debug logging
        print(f"🔍 DEBUG: Posting review to {url}")
        print(f"📝 DEBUG: Review body length: {len(review_body)}")
        print(f"💬 DEBUG: Number of inline comments: {len(comments or [])}")
        
        if comments:
            print("📍 DEBUG: Inline comments being sent:")
            for i, comment in enumerate(comments, 1):
                print(f"  {i}. File: {comment.path}, Line: {comment.line}, Side: {comment.side}")
                print(f"     Body: {comment.body[:100]}...")
        
        try:
            print(f"🌐 DEBUG: Making GitHub API request to: {url}")
            print(f"📦 DEBUG: Request payload: {data}")
            
            response = requests.post(url, headers=self.headers, json=data)
            print(f"📡 DEBUG: GitHub API response status: {response.status_code}")
            print(f"📄 DEBUG: Response headers: {dict(response.headers)}")
            
            if response.status_code != 200:
                print(f"❌ DEBUG: GitHub API error response: {response.text}")
                print(f"❌ DEBUG: Response JSON: {response.json() if response.content else 'No content'}")
            else:
                print(f"✅ DEBUG: Response JSON: {response.json()}")
            
            response.raise_for_status()
            print("✅ DEBUG: Review posted successfully")
            return True
            
        except requests.RequestException as e:
            print(f"❌ DEBUG: Error posting PR review: {e}")
            if hasattr(e, 'response') and e.response is not None:
                print(f"❌ DEBUG: Response status: {e.response.status_code}")
                print(f"❌ DEBUG: Response content: {e.response.text}")
                try:
                    print(f"❌ DEBUG: Response JSON: {e.response.json()}")
                except:
                    print("❌ DEBUG: Could not parse response as JSON")
            return False
    
    def parse_webhook_pr(self, webhook_data: Dict) -> Optional[Dict]:
        """
        Parse GitHub webhook data for pull request events
        
        Returns:
            Dictionary with PR info or None if not a PR event
        """
        if "pull_request" not in webhook_data:
            return None
            
        pr = webhook_data["pull_request"]
        repo = webhook_data["repository"]
        
        return {
            "action": webhook_data.get("action"),
            "pr_number": pr["number"],
            "pr_title": pr["title"],
            "pr_url": pr["html_url"],
            "repo_owner": repo["owner"]["login"],
            "repo_name": repo["name"],
            "repo_full_name": repo["full_name"],
            "author": pr["user"]["login"],
            "branch": pr["head"]["ref"],
            "base_branch": pr["base"]["ref"]
        }

    def fetch_pr_file_patches(self, repo_owner: str, repo_name: str, pr_number: int):
        """
        Fetch individual file patches from GitHub API for more accurate position mapping
        
        Returns:
            List of dicts with {filename, patch, position_map}
        """
        import re
        
        url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/pulls/{pr_number}/files"
        
        try:
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            
            files = []
            for file_data in response.json():
                # Skip files without patches (binary, too large, etc.)
                if 'patch' not in file_data:
                    print(f"⚠️  DEBUG: Skipping {file_data['filename']} - no patch available")
                    continue
                
                # Build position map for this file
                position_map = self._build_position_map_from_patch(file_data['patch'])
                
                files.append({
                    "filename": file_data["filename"],
                    "patch": file_data["patch"], 
                    "position_map": position_map,
                    "additions": file_data.get("additions", 0),
                    "deletions": file_data.get("deletions", 0)
                })
                
                print(f"📁 DEBUG: Processed {file_data['filename']} - {len(position_map)} commentable lines")
            
            return files
            
        except requests.RequestException as e:
            print(f"❌ DEBUG: Error fetching PR file patches: {e}")
            return []
    
    def _build_position_map_from_patch(self, patch_text: str):
        """
        Build mapping from new-file line numbers to GitHub diff positions
        
        Args:
            patch_text: Individual file patch content
            
        Returns:
            Dict[int, int]: new_line_number -> github_position
        """
        import re
        
        position = 0  # GitHub position counter (0-based, continuous across hunks)
        new_line = None
        mapping = {}
        
        for raw_line in patch_text.splitlines():
            position += 1  # GitHub positions are 1-based
            line = raw_line.rstrip("\n")
            
            if line.startswith('@@'):
                # Parse hunk header: @@ -oldStart,oldLen +newStart,newLen @@
                match = re.search(r'\+(\d+)', line)
                new_line = int(match.group(1)) if match else None
                continue
            
            if new_line is None:
                # Still before first hunk content
                continue
            
            # Process hunk content
            tag = line[:1] if line else ' '
            if tag == '+':
                # Added line - commentable on right side
                mapping[new_line] = position
                new_line += 1
            elif tag == '-':
                # Deleted line - not commentable on right side, don't advance new_line
                pass
            else:
                # Context line - commentable
                mapping[new_line] = position
                new_line += 1
        
        return mapping

    def map_ai_diff_lines_to_github_positions(self, ai_comments, pr_files, full_diff):
        """
        Map AI diff line numbers to proper GitHub positions using per-file patches
        
        Args:
            ai_comments: List of AI comments with diff line numbers
            pr_files: List of file patches from fetch_pr_file_patches
            full_diff: The complete diff that AI analyzed
            
        Returns:
            List of properly mapped comments for GitHub API
        """
        # Step 1: Build mapping from AI diff lines to source file lines
        diff_to_source = self._build_diff_to_source_mapping(full_diff)
        
        # Step 2: Build mapping from source lines to files
        source_to_file = self._build_source_to_file_mapping(pr_files)
        
        mapped_comments = []
        
        for comment in ai_comments:
            ai_diff_line = comment['line']
            print(f"🔍 DEBUG: Processing AI diff line {ai_diff_line}")
            
            # Map diff line → source line
            source_line = diff_to_source.get(ai_diff_line)
            if not source_line:
                print(f"❌ DEBUG: No source line found for diff line {ai_diff_line}")
                continue
                
            print(f"📍 DEBUG: Diff line {ai_diff_line} → Source line {source_line}")
            
            # Find which file contains this source line
            target_file = None
            for file_info in pr_files:
                if source_line in file_info["position_map"]:
                    target_file = file_info
                    break
            
            if not target_file:
                print(f"❌ DEBUG: No file found containing source line {source_line}")
                continue
            
            # Map source line → GitHub position
            github_position = target_file["position_map"][source_line]
            
            mapped_comments.append({
                "path": target_file["filename"],
                "position": github_position,
                "body": f"**🚨 {comment['severity']}**: {comment['issue']}\n\n**Impact**: {comment['impact']}\n\n**Fix**: {comment['fix']}"
            })
            
            print(f"✅ DEBUG: Mapped AI line {ai_diff_line} → {target_file['filename']}:pos{github_position}")
        
        return mapped_comments

    def _build_diff_to_source_mapping(self, full_diff):
        """
        Build mapping from diff line numbers to source file line numbers
        
        Returns:
            Dict[int, int]: diff_line_number -> source_line_number
        """
        import re
        
        diff_to_source = {}
        current_source_line = None
        
        for diff_line_num, line in enumerate(full_diff.splitlines(), 1):
            if line.startswith('@@'):
                # Parse hunk header: @@ -old_start,old_len +new_start,new_len @@
                match = re.search(r'\+(\d+)', line)
                current_source_line = int(match.group(1)) if match else None
                print(f"📍 DEBUG: Hunk starts at source line {current_source_line}")
                
            elif current_source_line is not None:
                # Process content lines
                if line.startswith('+') and not line.startswith('+++'):
                    # Added line
                    diff_to_source[diff_line_num] = current_source_line
                    print(f"🎯 DEBUG: Diff line {diff_line_num} (+) → Source line {current_source_line}")
                    current_source_line += 1
                    
                elif line.startswith('-') and not line.startswith('---'):
                    # Deleted line - don't advance source line
                    pass
                    
                elif (line and not line.startswith('\\') and 
                      not line.startswith('diff') and not line.startswith('index')):
                    # Context line - advance source line
                    current_source_line += 1
        
        return diff_to_source

    def _build_source_to_file_mapping(self, pr_files):
        """
        Build mapping from source line numbers to file information
        
        Returns:
            Dict[int, dict]: source_line -> file_info
        """
        source_to_file = {}
        
        for file_info in pr_files:
            for source_line in file_info["position_map"].keys():
                source_to_file[source_line] = file_info
                
        return source_to_file

    def post_individual_pr_comments(self, repo_owner: str, repo_name: str, pr_number: int, comments, commit_sha: str):
        """
        Post individual comments to PR using the /comments API (alternative to reviews API)
        
        Args:
            repo_owner: Repository owner
            repo_name: Repository name  
            pr_number: Pull request number
            comments: List of comment objects with path, line, body
            commit_sha: The commit SHA to comment on
            
        Returns:
            bool: True if all comments posted successfully
        """
        if not comments:
            print("⚠️  DEBUG: No comments to post")
            return True
            
        print(f"🔄 DEBUG: Posting {len(comments)} individual comments using /comments API")
        
        success_count = 0
        for i, comment in enumerate(comments, 1):
            url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/pulls/{pr_number}/comments"
            
            # Use line number instead of position (key difference from reviews API)
            payload = {
                "body": comment["body"],
                "commit_id": commit_sha,
                "path": comment["path"],
                "line": comment["line"]  # This is the absolute line number in the file
            }
            
            print(f"🔄 DEBUG: Posting comment {i}/{len(comments)} to {comment['path']}:line{comment['line']}")
            
            try:
                response = requests.post(url, headers=self.headers, json=payload)
                
                if response.status_code == 201:
                    print(f"✅ DEBUG: Comment {i} posted successfully")
                    success_count += 1
                else:
                    print(f"❌ DEBUG: Comment {i} failed - Status: {response.status_code}")
                    print(f"❌ DEBUG: Response: {response.text}")
                    
            except requests.RequestException as e:
                print(f"❌ DEBUG: Comment {i} failed with exception: {e}")
        
        print(f"📊 DEBUG: Posted {success_count}/{len(comments)} comments successfully")
        return success_count == len(comments)

    def get_pr_commit_sha(self, repo_owner: str, repo_name: str, pr_number: int):
        """
        Get the latest commit SHA for a pull request
        
        Returns:
            str: The latest commit SHA or None if failed
        """
        url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/pulls/{pr_number}/commits"
        
        try:
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            
            commits = response.json()
            if commits:
                latest_commit_sha = commits[-1]['sha']
                print(f"✅ DEBUG: Latest commit SHA: {latest_commit_sha}")
                return latest_commit_sha
            else:
                print("❌ DEBUG: No commits found in PR")
                return None
                
        except requests.RequestException as e:
            print(f"❌ DEBUG: Failed to get commit SHA: {e}")
            return None

    def map_ai_comments_to_line_numbers(self, ai_comments, full_diff):
        """
        Map AI diff line numbers to absolute file line numbers for individual comments API
        
        Args:
            ai_comments: List of AI comments with diff line numbers
            full_diff: The complete diff content
            
        Returns:
            List of comments with absolute line numbers for individual comments API
        """
        print(f"🔄 DEBUG: Mapping {len(ai_comments)} AI comments to absolute line numbers")
        
        # Build mapping from diff lines to absolute file lines
        diff_to_absolute = {}
        current_file = None
        
        for diff_line_num, line in enumerate(full_diff.splitlines(), 1):
            if line.startswith('diff --git '):
                # Extract file path
                parts = line.split(' ')
                if len(parts) >= 4:
                    b_path = parts[3]
                    current_file = b_path[2:] if b_path.startswith('b/') else b_path
                    print(f"📁 DEBUG: Processing file: {current_file}")
                    
            elif line.startswith('@@'):
                # Parse hunk header to get starting line number
                import re
                match = re.search(r'\+(\d+)', line)
                if match:
                    start_line = int(match.group(1))
                    print(f"📍 DEBUG: Hunk starts at line {start_line}")
                    
                    # Map subsequent added lines to absolute line numbers
                    current_absolute_line = start_line
                    
            elif current_file and line.startswith('+') and not line.startswith('+++'):
                # This is an added line - map it
                diff_to_absolute[diff_line_num] = {
                    'file_path': current_file,
                    'absolute_line': current_absolute_line
                }
                print(f"🎯 DEBUG: Diff line {diff_line_num} → {current_file}:line{current_absolute_line}")
                current_absolute_line += 1
                
            elif current_file and not line.startswith('-') and not line.startswith('+++') and not line.startswith('---'):
                # Context line - advance absolute line counter
                if 'current_absolute_line' in locals():
                    current_absolute_line += 1
        
        # Map AI comments to absolute line numbers
        mapped_comments = []
        for comment in ai_comments:
            ai_diff_line = comment['line']
            
            if ai_diff_line in diff_to_absolute:
                mapping = diff_to_absolute[ai_diff_line]
                mapped_comments.append({
                    "path": mapping['file_path'],
                    "line": mapping['absolute_line'],
                    "body": f"**🚨 {comment['severity']}**: {comment['issue']}\n\n**Impact**: {comment['impact']}\n\n**Fix**: {comment['fix']}"
                })
                print(f"✅ DEBUG: Mapped AI diff line {ai_diff_line} → {mapping['file_path']}:line{mapping['absolute_line']}")
            else:
                print(f"❌ DEBUG: Could not map AI diff line {ai_diff_line}")
        
        print(f"✅ DEBUG: Successfully mapped {len(mapped_comments)}/{len(ai_comments)} comments")
        return mapped_comments

# Global service instance  
github_service = GitHubService() 
