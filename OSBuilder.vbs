Set WshShell = CreateObject("WScript.Shell")
appDir = CreateObject("Scripting.FileSystemObject").GetParentFolderName(WScript.ScriptFullName)
exePath = appDir & "\OSBuilder-Win.exe"

If CreateObject("Scripting.FileSystemObject").FileExists(exePath) Then
    WshShell.Run Chr(34) & exePath & Chr(34), 1, False
Else
    pythonwPath = "C:\Users\madtr\AppData\Local\Programs\Python\Python312\pythonw.exe"
    guiPath = appDir & "\gui.py"
    WshShell.CurrentDirectory = appDir
    WshShell.Run Chr(34) & pythonwPath & Chr(34) & " " & Chr(34) & guiPath & Chr(34), 1, False
End If
