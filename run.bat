@echo off
title Course Progress Tracker

REM --------------------------------------------------
REM Activate conda environment
REM (Update this path if Anaconda is installed elsewhere)
REM --------------------------------------------------
call "%USERPROFILE%\anaconda3\Scripts\activate.bat" ds_env
IF ERRORLEVEL 1 (
    echo Failed to activate conda environment: ds_env
    pause
    exit /b
)

REM --------------------------------------------------
REM Run Streamlit app
REM The current folder (course root) is passed automatically
REM --------------------------------------------------
streamlit run "F:\Projects\Course-Progress-Tracker\app.py" -- "%CD%"

REM --------------------------------------------------
REM Keep window open if Streamlit exits
REM --------------------------------------------------
pause
