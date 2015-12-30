@echo off
echo building UniBox Service Controller...
echo Author wangXi(wangxi@unibox.com.cn)
echo --------------------------------------
REM echo newline
echo. &

rem first remove previous installed sync svc
SC QUERY UniboxSvc
NET STOP UniboxSvc
SC DELETE UniboxSvc

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

if exist ubsc.spec (
    del ubsc.spec
)

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
if not exist %PYTHON_HOME%\Lib\site-packages\PyInstaller-3.0-py2.7.egg (
    cd deps/PyInstaller-3.0
    python setup.py install
    cd ../..

    goto PAC_EXE
)

:PAC_EXE
REM list all packages in system
REM python -m pip list
python -m PyInstaller --clean --onefile --icon=app.ico ubsc.py

echo removing build dir...
if exist build (
    rd build /s/q
)

echo starting ubsc...

rem cd /d dist

rem sync -c auto
rem sync -c start
rem pause

:END_CALL
rem cd /d ..
cmd /c start start_ubsc.bat
