@echo off

rem Replace "path\to\your\anaconda3" with the actual path to your Anaconda installation
set ANACONDA_PATH="C:\ProgramData\anaconda3"

rem Replace "code3" with the name of your environment
set ENV_NAME=code3

rem Check if the Anaconda installation directory exists
if not exist %ANACONDA_PATH% (
    echo Anaconda directory not found. Please update the ANACONDA_PATH variable.
    pause
    exit /b 1
)

rem Activate the Anaconda environment
call %ANACONDA_PATH%\Scripts\activate %ENV_NAME%

if %errorlevel% neq 0 (
    echo Failed to activate the environment %ENV_NAME%.
    pause
    exit /b 1
)

rem Change the working directory and run server
cd "C:\Users\Cryo_rdyberg\Documents\Codebase\Lab_control\servers\parameter_vault"
python "parameter_vault.py"



rem Start Anaconda Navigator or any other command you want to execute
rem start %ANACONDA_PATH%\Scripts\anaconda-navigator.exe

rem echo Activated Anaconda environment: %ENV_NAME%