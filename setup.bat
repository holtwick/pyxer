c:\Python25\python.exe setup_version.py
rem pisa -s docs\*.html
xcopy docs\*.* example\docs /S /Y
c:\Python25\python.exe setup.py sdist -k
pause
