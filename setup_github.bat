@echo off
echo ========================================
echo GitHub Setup for CMPE148 Chat Project
echo Team No Sleep
echo ========================================
echo.

echo Step 1: Checking git status...
git status
echo.

echo Step 2: Adding all files...
git add .
echo.

echo Step 3: Committing...
git commit -m "Complete custom chat protocol implementation - CMPE 148 Team No Sleep"
echo.

echo ========================================
echo NEXT STEPS (DO THESE MANUALLY):
echo ========================================
echo.
echo 1. Go to: https://github.com/new
echo 2. Repository name: CMPE148-Chat-Protocol
echo 3. Description: Custom Application-Layer Protocol for Reliable Chat
echo 4. Choose Private or Public
echo 5. DO NOT initialize with README
echo 6. Click "Create repository"
echo.
echo 7. After creating, GitHub will show commands like this:
echo    git remote add origin https://github.com/YOUR-USERNAME/CMPE148-Chat-Protocol.git
echo    git branch -M main
echo    git push -u origin main
echo.
echo 8. Copy those commands and paste them here!
echo.
echo Press any key when you've created the repository on GitHub...
pause > nul
echo.
echo Now paste the commands GitHub gave you below:
echo.

cmd /k
