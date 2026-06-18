Set shell = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")
scriptDir = fso.GetParentFolderName(WScript.ScriptFullName)
shell.Run "pythonw.exe """ & scriptDir & "\ai_billedbeskriver_gui.pyw""", 0, False
