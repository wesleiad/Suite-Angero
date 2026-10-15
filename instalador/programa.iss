; Instalador avulso de um programa da Suíte Angerô (Inno Setup 6).
; Compilado por montar_instaladores.ps1 (ou pelo GitHub Actions) com:
;   ISCC /DId=illustre /DNome="Illustre - Angerô" /DExe=illustre /DIcone=vetor /DArgs="--control 7979"
;        /DVersao=1.0.0.1 /DFonte=<pasta com os .exe> /DIcones=<pasta icones\ico> /DSaida=<pasta> programa.iss
; Instala por usuário (sem senha de administrador), para a Suíte conseguir atualizar sozinha.

#ifndef Args
  #define Args ""
#endif

; pasta usada pelas associações de arquivo (assoc\<id>.iss)
#define AppPasta_illustre "{app}"
#define AppPasta_fotografe "{app}"
#define AppPasta_pdf "{app}"
#define AppPasta_cena "{app}"
#define AppPasta_lightbridge "{app}"

[Setup]
AppId={{Suite-Angero-{#Id}}
AppName={#Nome}
AppVersion={#Versao}
AppVerName={#Nome} {#Versao}
AppPublisher=Grupo Angerô
AppPublisherURL=https://github.com/wesleiad/Suite-Angero
AppSupportURL=https://github.com/wesleiad/Suite-Angero/blob/main/docs/ajuda/{#Id}.md
DefaultDirName={localappdata}\Programs\Suite Angero\{#Nome}
DefaultGroupName=Suíte Angerô
DisableProgramGroupPage=yes
DisableDirPage=yes
PrivilegesRequired=lowest
OutputDir={#Saida}
OutputBaseFilename=Instalar {#Nome}
SetupIconFile={#Icones}\{#Icone}.ico
UninstallDisplayIcon={app}\{#Exe}.exe
UninstallDisplayName={#Nome}
WizardStyle=modern
Compression=lzma2/max
SolidCompression=yes
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
CloseApplications=yes
ChangesAssociations=yes
VersionInfoCompany=Grupo Angerô
VersionInfoProductName={#Nome}
VersionInfoVersion={#Versao}

[Languages]
Name: "pt"; MessagesFile: "compiler:Languages\BrazilianPortuguese.isl"

[Tasks]
Name: "associar"; Description: "Usar o {#Nome} como programa padrão para os arquivos dele"; GroupDescription: "Arquivos:"
Name: "atalho"; Description: "Criar atalho na Área de Trabalho"; GroupDescription: "Atalhos:"

[Files]
Source: "{#Fonte}\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "{#Icones}\{#Icone}.ico"; DestDir: "{app}"; DestName: "icone.ico"; Flags: ignoreversion

[Icons]
Name: "{group}\{#Nome}"; Filename: "{app}\{#Exe}.exe"; Parameters: "{#Args}"; IconFilename: "{app}\icone.ico"
Name: "{userdesktop}\{#Nome}"; Filename: "{app}\{#Exe}.exe"; Parameters: "{#Args}"; IconFilename: "{app}\icone.ico"; Tasks: atalho

[Registry]
; a Suíte Angerô procura os programas instalados por aqui
Root: HKCU; Subkey: "Software\Grupo Angero\Suite Angero\Programas\{#Id}"; ValueType: string; ValueName: "Pasta"; ValueData: "{app}"; Flags: uninsdeletekey
Root: HKCU; Subkey: "Software\Grupo Angero\Suite Angero\Programas\{#Id}"; ValueType: string; ValueName: "Versao"; ValueData: "{#Versao}"

#include AddBackslash(SourcePath) + "assoc\" + Id + ".iss"

[Run]
Filename: "{app}\{#Exe}.exe"; Parameters: "{#Args}"; Description: "Abrir o {#Nome}"; Flags: nowait postinstall skipifsilent
