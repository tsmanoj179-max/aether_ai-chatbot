' ==============================================================================
' AetherAI Universal Application Launcher (Completely Silent / No Terminals)
' ==============================================================================
Option Explicit

Dim objShell, objFSO, strDir, strPythonw, strScript

Set objShell = CreateObject("WScript.Shell")
Set objFSO = CreateObject("Scripting.FileSystemObject")

' Set working directory to project root
strDir = objFSO.GetParentFolderName(WScript.ScriptFullName)
objShell.CurrentDirectory = strDir

' Locate pythonw in virtual environment or fallback to system
strPythonw = strDir & "\.venv\Scripts\pythonw.exe"
If Not objFSO.FileExists(strPythonw) Then
    strPythonw = "pythonw.exe"
End If

strScript = strDir & "\aether_app.py"

' Run pythonw completely hidden (WindowStyle = 0: SW_HIDE)
objShell.Run """" & strPythonw & """ """ & strScript & """", 0, False

Set objShell = Nothing
Set objFSO = Nothing
