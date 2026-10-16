; Instalador do Editor Visual da Suíte Angerô (ferramenta do TI) — Inno Setup 6.
; Compilar (da pasta instalador\):
;   ISCC /DVersao=1.0.0.0 /DPython=<build\python portátil> /DSaida=<pasta de saída> editor_visual.iss
; Instala por usuário (sem senha de administrador). Na primeira abertura o Editor baixa (git clone) o
; código dos 5 programas; para "Publicar" a máquina precisa do Git e de login no GitHub com acesso de
; escrita aos repositórios wesleiad/*-angero.

#define Raiz AddBackslash(SourcePath) + ".."

[Setup]
AppId={{Suite-Angero-editor-visual}
AppName=Editor Visual - Suíte Angerô
AppVersion={#Versao}
AppVerName=Editor Visual - Suíte Angerô {#Versao}
AppPublisher=Grupo Angerô
AppPublisherURL=https://github.com/wesleiad/Suite-Angero
AppCopyright=© 2026 Weslei Domingues
DefaultDirName={localappdata}\Programs\Suite Angero\Editor Visual
DefaultGroupName=Suíte Angerô
DisableProgramGroupPage=yes
DisableDirPage=yes
PrivilegesRequired=lowest
OutputDir={#Saida}
OutputBaseFilename=Instalar Editor Visual - Angerô
SetupIconFile={#Raiz}\icones\ico\editor.ico
UninstallDisplayIcon={app}\icone.ico
UninstallDisplayName=Editor Visual - Suíte Angerô
WizardStyle=modern
Compression=lzma2/max
SolidCompression=yes
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
VersionInfoCompany=Grupo Angerô
VersionInfoProductName=Editor Visual - Suíte Angerô
VersionInfoVersion={#Versao}

[Languages]
Name: "pt"; MessagesFile: "compiler:Languages\BrazilianPortuguese.isl"

[Tasks]
Name: "atalho"; Description: "Criar atalho na Área de Trabalho"; GroupDescription: "Atalhos:"

[Files]
Source: "{#Python}\*"; DestDir: "{app}\python"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "{#Raiz}\ferramentas\editor_visual.py"; DestDir: "{app}"; Flags: ignoreversion
Source: "{#Raiz}\ferramentas\editor_visual.html"; DestDir: "{app}"; Flags: ignoreversion
Source: "{#Raiz}\icones\ico\editor.ico"; DestDir: "{app}"; DestName: "icone.ico"; Flags: ignoreversion
Source: "{#Raiz}\LICENSE"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\Editor Visual - Suíte Angerô"; Filename: "{app}\python\pythonw.exe"; Parameters: """{app}\editor_visual.py"""; WorkingDir: "{app}"; IconFilename: "{app}\icone.ico"
Name: "{userdesktop}\Editor Visual - Suíte Angerô"; Filename: "{app}\python\pythonw.exe"; Parameters: """{app}\editor_visual.py"""; WorkingDir: "{app}"; IconFilename: "{app}\icone.ico"; Tasks: atalho

[Run]
Filename: "{app}\python\pythonw.exe"; Parameters: """{app}\editor_visual.py"""; WorkingDir: "{app}"; Description: "Abrir o Editor Visual"; Flags: nowait postinstall skipifsilent
