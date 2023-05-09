@echo off

if [%1]==[] goto help

REM This allows us to expand variables at execution
setlocal ENABLEDELAYEDEXPANSION

REM This will set DIFF as a list of staged files
set DIFF=
for /F "tokens=* USEBACKQ" %%A in (`git diff --name-only --staged "*.py" "*.pyi"`) do (
    set DIFF=!DIFF! %%A
)

REM This will set DIFF as a list of files tracked by git
if [!DIFF!]==[] (
    set DIFF=
    for /F "tokens=* USEBACKQ" %%A in (`git ls-files "*.py" "*.pyi"`) do (
        set DIFF=!DIFF! %%A
    )
)

goto %1

:installreqs
pip install --upgrade flake8 autoflake isort black
goto :eof

:lint
flake8 --count --select=E9,F63,F7,F82 --show-source --statistics !DIFF!
goto :eof

:stylecheck
autoflake --check !DIFF! || goto :eof
isort --check-only !DIFF! || goto :eof
black --check !DIFF!
goto :eof

:reformat
autoflake --in-place !DIFF! || goto :eof
isort !DIFF! || goto :eof
black !DIFF!
goto :eof

:help
echo Usage:
echo   make ^<command^>
echo.
echo Commands:
echo   lint                         Lints .py files using flake8
echo   stylecheck                   Check that all .py files meet style guidelines.
echo   reformat                     Reformat all .py files being tracked by git.
