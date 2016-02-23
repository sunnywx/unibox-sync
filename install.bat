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

    goto STOP_ORIG_SVC

) else (
    echo 'uniboxSvc not running'
)

rem first remove previous installed sync svc
:STOP_ORIG_SVC
SC QUERY UniboxSvc
NET STOP UniboxSvc
rem SC DELETE UniboxSvc

rem remove original svc if exists
rem NET STOP UniboxSyncService
rem SC DELETE UniboxSyncService

REM if not change to current dir
REM when use adminstrator in windows
REM cmd start dir is %windir%\system32 will raise error

REM see: http://weblogs.asp.net/whaggard/get-directory-path-of-an-executing-batch-file
@setlocal enableextensions
rem pushd "%CD%"
@cd /d "%~dp0"

set BUILD_DIR=%~dp0

REM assume python PATH is c:\python27
REM temporally add python.exe to current shell path
set PYTHON_HOME=C:\python27
REM set include path temporarily
set PATH=%PATH%;%PYTHON_HOME%;%PYTHON_HOME%\Scripts;

echo checking python environment...
if not exist %PYTHON_HOME%\python.exe (
    echo python2.7 is not installed, please install python2.7
    rem depend\python-2.7.10.msi
    pause
    exit

    rem echo python installed, begin compiling Sync application...
    rem goto BEGIN_COMPILE_SYNC
)

:BEGIN_COMPILE
REM only on kiosk deploy
rem if exist dist\sync\sync.exe (
rem     goto END_CALL
rem )

REM dev mode
if exist dist (
    rd dist /s/q
)
REM start rebuild sync.exe, clear previous build tmp
if exist build (
    rd build /s/q
)

if exist ubx.spec (
    del ubx.spec
)

rem clearing .pyc
rem for /r %f in (*.pyc) do del %f
del /s *.pyc

echo building requirements...
REM python -m pip install pywin32
REM python -m pip install pyinstaller
REM python -m pip install -r requirements.txt
REM first install py-win32, then py-installer
if not exist %PYTHON_HOME%\Lib\site-packages\pywin32_system32 (
    depend\pywin32-219.win32-py2.7.exe
    goto PY_PSUTIL
)

:PY_PSUTIL
if not exist %PYTHON_HOME%\Lib\site-packages\psutil (
    depend\psutil-3.3.0.win32-py2.7.exe
    goto PY_INSTALLER
)

:PY_INSTALLER
rem if not exist %PYTHON_HOME%\Lib\site-packages\PyInstaller-3.0-py2.7.egg (
rem     cd depend/PyInstaller
rem     python setup.py install
rem     cd ../..
rem     goto PAC_EXE
rem )

pip install PyInstaller

:PAC_EXE
REM list all packages in system
REM python -m pip list
python -m PyInstaller --clean --onefile ubx.py

echo removing tmp directory...
if exist build (
    rd build /s/q
)

rem create app ini
if not exist apps\Sync\sync_app.ini (
    echo rename [sync_app.ini.sample] to [sync_app.ini]
    copy apps\Sync\sync_app.ini.sample apps\Sync\sync_app.ini
)

if not exist apps\Monitor\monitor_app.ini (
    echo rename [monitor_app.ini.sample] to [monitor_app.ini]
    copy apps\Monitor\monitor_app.ini.sample apps\Monitor\monitor_app.ini
)

echo starting uniboxSvc...

cd /d dist

ubx auto
ubx start

rem post-install set app version
git --version 2>nul
if "%ERRORLEVEL%"=="0" (
    ubx -g
)

rem pause

:END_CALL
cd /d ..

echo. &
echo starting cli program...
cmd /c cli.bat