# Git + Zsh Cheat Sheet

```zsh
# ============================================
# TERMINAL / ZSH
# ============================================

pwd                     # Show current directory
ls                      # List files
ls -la                  # List all files, including hidden files
cd folder-name          # Enter a folder
cd ..                   # Go back one folder
cd ~                    # Go to home directory
mkdir folder-name       # Create a folder
touch filename          # Create an empty file
clear                   # Clear terminal
code .                  # Open current folder in VS Code


# ============================================
# STARTING WITH GIT
# ============================================

git init
# Initialize Git in the current folder

git clone <repository-url>
# Download/clone an existing repository


# ============================================
# CHECK STATUS / CHANGES
# ============================================

git status
# Check changed, staged, and untracked files

git diff
# See unstaged changes

git diff --staged
# See staged changes

git log
# See commit history

git log --oneline
# See simplified commit history

git remote -v
# See connected remote repository


# ============================================
# STAGING FILES
# ============================================

git add .
# Stage ALL changes

git add filename
# Stage one specific file


# ============================================
# COMMIT
# ============================================

git commit -m "Your commit message"

# Example:
git commit -m "Add weather data ingestion"


# ============================================
# PUSH
# ============================================

git push
# Push commits to remote repository

git push origin main
# Push main branch to origin


# ============================================
# PULL
# ============================================

git pull
# Get latest remote changes

git pull origin main
# Get latest changes from main


# ============================================
# BRANCHES
# ============================================

git branch
# Show branches

git branch branch-name
# Create a new branch

git switch branch-name
# Switch to a branch

git switch -c branch-name
# Create AND switch to a new branch

git merge branch-name
# Merge branch into current branch

git branch -d branch-name
# Delete a local branch


# ============================================
# UNDO / FIX
# ============================================

git restore filename
# Discard unstaged changes to a file

git restore --staged filename
# Remove file from staging without deleting changes

git commit --amend
# Modify the most recent commit


# ============================================
# MY NORMAL GIT WORKFLOW
# ============================================

# 1. Check current status
git status

# 2. Get latest changes
git pull

# 3. Make changes to files...

# 4. Check what changed
git status

# 5. Stage changes
git add .

# 6. Commit changes
git commit -m "Describe what I changed"

# 7. Push changes
git push


# ============================================
# 5 COMMANDS TO MEMORIZE
# ============================================

git status
git pull
git add .
git commit -m "message"
git push


# ============================================
# WHEN CONFUSED
# ============================================

git status
```