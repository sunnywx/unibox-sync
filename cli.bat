@echo off
@setlocal enableextensions
rem pushd "%CD%"
@cd /d "%~dp0"

cd /d dist

REM hold current window
cmd /k ubx
