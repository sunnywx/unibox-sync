@echo off
echo building py-ubx...
echo Author: wangXi(iwisunny@gmail.com)
echo --------------------------------------
REM echo newline
echo. &

tasklist /FI "IMAGENAME eq pythonservice.exe" 2>NUL | find /I /N "pythonservice.exe">NUL
if "%ERRORLEVEL%"=="0" (
    echo uniboxSvc is running, kill it

    rem force kill pythonservice.exe which hosts py-ubx
    taskkill /f /im pythonservice.exe

) else (
    echo uniboxSvc not running
)

REM change to current dir
REM see: http://weblogs.asp.net/whaggard/get-directory-path-of-an-executing-batch-file
@setlocal enableextensions
rem pushd "%CD%"
@cd /d "%~dp0"

set BUILD_DIR=%~dp0

REM assume python PATH is c:\python27
REM temporally add python.exe to current shell path
set PYTHON_HOME=C:\python27

echo checking python environment...
if not exist %PYTHON_HOME%\python.exe (
    echo python is not installed, please first install it
    pause
    exit
)

REM set include path temporarily
set PATH=%PATH%;%PYTHON_HOME%;%PYTHON_HOME%\Scripts;

REM dev mode
if exist dist (
    rd dist /s/q
)

REM start rebuild ubx.exe, clear previous build tmp dir
if exist build (
    rd build /s/q
)

if exist ubx.spec (
    del ubx.spec
)

rem clearing .pyc
rem for /r %f in (*.pyc) do del %f
del /s *.pyc

echo building py-ubx dependencies...
python -m pip install -r requirements.txt

python ubx.py --util dl_deps

rem if not exist %PYTHON_HOME%\Lib\site-packages\pywin32_system32 (
rem     python ubx.py --util dl_deps
rem     deps\pywin32-219.win32-py2.7.exe
rem )

REM python -m pip list
python -m PyInstaller --clean --onefile ubx.py

if exist build (
    rd build /s/q
)

rem setup app ini
if not exist apps\Sync\sync_app.ini (
    echo copy [sync_app.ini.sample] to [sync_app.ini]
    copy apps\Sync\sync_app.ini.sample apps\Sync\sync_app.ini
)

if not exist apps\Monitor\monitor_app.ini (
    echo copy [monitor_app.ini.sample] to [monitor_app.ini]
    copy apps\Monitor\monitor_app.ini.sample apps\Monitor\monitor_app.ini
)

python ubx.py --util db_mig

echo [svc] starting uniboxSvc...
cd /d dist
ubx auto
ubx start

:END_CALL
cd /d ..

rem echo. &
rem echo starting cli program...
rem cmd /c cli.bat