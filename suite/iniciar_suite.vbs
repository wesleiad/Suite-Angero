' Inicia a Suíte Angerô sem janela de console (servidor local + janela do iniciador).
Set fso = CreateObject("Scripting.FileSystemObject")
pasta = fso.GetParentFolderName(WScript.ScriptFullName)
Set sh = CreateObject("WScript.Shell")
sh.CurrentDirectory = pasta
' Python portátil do pacote, se existir; senão o pythonw instalado
py = fso.BuildPath(pasta, "..\python\pythonw.exe")
If Not fso.FileExists(py) Then py = "pythonw"
' Repassa os argumentos do atalho (ex.: --abrir vetor, --fluxogama)
args = ""
For Each a In WScript.Arguments
  args = args & " """ & a & """"
Next
sh.Run """" & py & """ """ & fso.BuildPath(pasta, "servidor.py") & """" & args, 0, False
