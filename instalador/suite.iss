; Instalador da Suíte Angerô completa: iniciador + Assistente de IA + extensões + os 5 programas.
; Compilado por montar_instaladores.ps1 (ou pelo GitHub Actions) com:
;   ISCC /DVersao=1.0.0.1 /DArqVersao=<versao.txt> /DRaiz=<repo Suite-Angero> /DPython=<python portátil> /DProgramas=<pasta com uma
;        subpasta por programa: illustre\, fotografe\, pdf\, cena\, lightbridge\> /DSaida=<pasta> suite.iss
; Instala por usuário (sem senha de administrador): a Suíte se atualiza sozinha.

#define Base "{localappdata}\Programs\Suite Angero"
#define Reg "Software\Grupo Angero\Suite Angero\Programas"
; pastas dos programas (associações de arquivo em assoc\<id>.iss)
#define AppPasta_illustre Base + "\Illustre - Angerô"
#define AppPasta_fotografe Base + "\Fotografe - Angerô"
#define AppPasta_pdf Base + "\PDF - Angerô"
#define AppPasta_cena Base + "\Cena - Angerô"
#define AppPasta_lightbridge Base + "\LightBridge - Angerô"
; O Windows guarda a imagem de cada ícone pelo caminho do arquivo: gravar o ícone novo com o mesmo
; nome deixava os atalhos com o ícone antigo nos PCs que já tinham uma versão anterior. Por isso o
; nome muda a cada versão, os antigos são apagados e, no fim, o cache de ícones é recarregado.
#define ArqIcone "icone-" + Versao + ".ico"
; o Illustre abre pela Suíte, para o botão Extensões aparecer
#define Cmd_illustre '""{sys}\wscript.exe"" ""{app}\suite\iniciar_suite.vbs"" --abrir vetor --arquivo ""%1""'

[Setup]
AppId={{Suite-Angero-Suite}
AppName=Suíte Angerô
AppVersion={#Versao}
AppVerName=Suíte Angerô {#Versao}
AppPublisher=Grupo Angerô
AppPublisherURL=https://github.com/wesleiad/Suite-Angero
AppSupportURL=https://github.com/wesleiad/Suite-Angero/blob/main/docs/ajuda/suite.md
DefaultDirName={#Base}\Suite
DefaultGroupName=Suíte Angerô
DisableProgramGroupPage=yes
DisableDirPage=yes
PrivilegesRequired=lowest
OutputDir={#Saida}
OutputBaseFilename=Instalar Suíte Angerô
SetupIconFile={#Raiz}\icones\ico\suite.ico
UninstallDisplayIcon={app}\suite-{#Versao}.ico
UninstallDisplayName=Suíte Angerô
WizardStyle=modern
Compression=lzma2/max
SolidCompression=yes
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
CloseApplications=yes
ChangesAssociations=yes
VersionInfoCompany=Grupo Angerô
VersionInfoProductName=Suíte Angerô
VersionInfoVersion={#Versao}

[Languages]
Name: "pt"; MessagesFile: "compiler:Languages\BrazilianPortuguese.isl"

[Tasks]
Name: "associar"; Description: "Usar os programas da Suíte como padrão para os arquivos deles (.ai, .psd, .pdf...)"; GroupDescription: "Arquivos:"
Name: "atalhos"; Description: "Criar atalhos na Área de Trabalho"; GroupDescription: "Atalhos:"

[InstallDelete]
Type: files; Name: "{#AppPasta_illustre}\icone*.ico"
Type: files; Name: "{#AppPasta_fotografe}\icone*.ico"
Type: files; Name: "{#AppPasta_pdf}\icone*.ico"
Type: files; Name: "{#AppPasta_cena}\icone*.ico"
Type: files; Name: "{#AppPasta_lightbridge}\icone*.ico"
Type: files; Name: "{app}\suite-*.ico"

[Files]
; iniciador, assistente e extensões
Source: "{#Python}\*"; DestDir: "{app}\python"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "{#Raiz}\suite\*"; DestDir: "{app}\suite"; Excludes: "__pycache__,*.pyc"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "{#Raiz}\icones\ico\*"; DestDir: "{app}\icones\ico"; Flags: ignoreversion
Source: "{#Raiz}\icones\png\*"; DestDir: "{app}\icones\png"; Flags: ignoreversion
Source: "{#Raiz}\icones\svg\*"; DestDir: "{app}\icones\svg"; Flags: ignoreversion
Source: "{#Raiz}\docs\*"; DestDir: "{app}\docs"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "{#Raiz}\plugins\*"; DestDir: "{app}\plugins"; Flags: ignoreversion recursesubdirs createallsubdirs skipifsourcedoesntexist
Source: "{#Raiz}\LICENSE"; DestDir: "{app}"; Flags: ignoreversion
Source: "{#Raiz}\README.md"; DestDir: "{app}"; Flags: ignoreversion
Source: "{#ArqVersao}"; DestDir: "{app}"; DestName: "versao.txt"; Flags: ignoreversion
Source: "{#ArqVersao}"; DestDir: "{app}"; DestName: "instalado.txt"; Flags: ignoreversion
; os programas (cada um na sua pasta, como nos instaladores avulsos)
Source: "{#Programas}\illustre\*"; DestDir: "{#Base}\Illustre - Angerô"; Flags: ignoreversion recursesubdirs
Source: "{#Programas}\fotografe\*"; DestDir: "{#Base}\Fotografe - Angerô"; Flags: ignoreversion recursesubdirs
Source: "{#Programas}\pdf\*"; DestDir: "{#Base}\PDF - Angerô"; Flags: ignoreversion recursesubdirs
Source: "{#Programas}\cena\*"; DestDir: "{#Base}\Cena - Angerô"; Flags: ignoreversion recursesubdirs
Source: "{#Programas}\lightbridge\*"; DestDir: "{#Base}\LightBridge - Angerô"; Flags: ignoreversion recursesubdirs

Source: "{#Raiz}\icones\ico\vetor.ico"; DestDir: "{#AppPasta_illustre}"; DestName: "{#ArqIcone}"; Flags: ignoreversion
Source: "{#Raiz}\icones\ico\foto.ico"; DestDir: "{#AppPasta_fotografe}"; DestName: "{#ArqIcone}"; Flags: ignoreversion
Source: "{#Raiz}\icones\ico\pdf.ico"; DestDir: "{#AppPasta_pdf}"; DestName: "{#ArqIcone}"; Flags: ignoreversion
Source: "{#Raiz}\icones\ico\video.ico"; DestDir: "{#AppPasta_cena}"; DestName: "{#ArqIcone}"; Flags: ignoreversion
Source: "{#Raiz}\icones\ico\galeria.ico"; DestDir: "{#AppPasta_lightbridge}"; DestName: "{#ArqIcone}"; Flags: ignoreversion
Source: "{#Raiz}\icones\ico\suite.ico"; DestDir: "{app}"; DestName: "suite-{#Versao}.ico"; Flags: ignoreversion

[Dirs]
Name: "{app}\plugins"

[Registry]
Root: HKCU; Subkey: "{#Reg}\illustre"; ValueType: string; ValueName: "Pasta"; ValueData: "{#Base}\Illustre - Angerô"; Flags: uninsdeletekey
Root: HKCU; Subkey: "{#Reg}\fotografe"; ValueType: string; ValueName: "Pasta"; ValueData: "{#Base}\Fotografe - Angerô"; Flags: uninsdeletekey
Root: HKCU; Subkey: "{#Reg}\pdf"; ValueType: string; ValueName: "Pasta"; ValueData: "{#Base}\PDF - Angerô"; Flags: uninsdeletekey
Root: HKCU; Subkey: "{#Reg}\cena"; ValueType: string; ValueName: "Pasta"; ValueData: "{#Base}\Cena - Angerô"; Flags: uninsdeletekey
Root: HKCU; Subkey: "{#Reg}\lightbridge"; ValueType: string; ValueName: "Pasta"; ValueData: "{#Base}\LightBridge - Angerô"; Flags: uninsdeletekey

#include AddBackslash(SourcePath) + "assoc\illustre.iss"
#include AddBackslash(SourcePath) + "assoc\fotografe.iss"
#include AddBackslash(SourcePath) + "assoc\pdf.iss"
#include AddBackslash(SourcePath) + "assoc\cena.iss"
#include AddBackslash(SourcePath) + "assoc\lightbridge.iss"

[Icons]
Name: "{group}\Suíte Angerô"; Filename: "{sys}\wscript.exe"; Parameters: """{app}\suite\iniciar_suite.vbs"""; IconFilename: "{app}\suite-{#Versao}.ico"
Name: "{group}\Illustre - Angerô"; Filename: "{sys}\wscript.exe"; Parameters: """{app}\suite\iniciar_suite.vbs"" --abrir vetor"; IconFilename: "{#AppPasta_illustre}\{#ArqIcone}"
Name: "{group}\Fotografe - Angerô"; Filename: "{#Base}\Fotografe - Angerô\fotografe.exe"; Parameters: "--control 7981 --control-token-file {localappdata}\SuiteAngero\fotografe.token"; IconFilename: "{#AppPasta_fotografe}\{#ArqIcone}"
Name: "{group}\PDF - Angerô"; Filename: "{#Base}\PDF - Angerô\pdf-angero.exe"; IconFilename: "{#AppPasta_pdf}\{#ArqIcone}"
Name: "{group}\Cena - Angerô"; Filename: "{#Base}\Cena - Angerô\cena.exe"; Parameters: "--control 7982"; IconFilename: "{#AppPasta_cena}\{#ArqIcone}"
Name: "{group}\LightBridge - Angerô"; Filename: "{#Base}\LightBridge - Angerô\lightbridge.exe"; Parameters: "--control 7980"; IconFilename: "{#AppPasta_lightbridge}\{#ArqIcone}"
#ifexist AddBackslash(Raiz) + "plugins\fluxogama\CSXS\manifest.xml"
Name: "{group}\Fluxogama - Angerô"; Filename: "{sys}\wscript.exe"; Parameters: """{app}\suite\iniciar_suite.vbs"" --fluxogama"; IconFilename: "{app}\icones\ico\fluxogama.ico"
#endif
Name: "{userdesktop}\Suíte Angerô"; Filename: "{sys}\wscript.exe"; Parameters: """{app}\suite\iniciar_suite.vbs"""; IconFilename: "{app}\suite-{#Versao}.ico"; Tasks: atalhos
Name: "{userdesktop}\Illustre - Angerô"; Filename: "{sys}\wscript.exe"; Parameters: """{app}\suite\iniciar_suite.vbs"" --abrir vetor"; IconFilename: "{#AppPasta_illustre}\{#ArqIcone}"; Tasks: atalhos

[Run]
Filename: "{sys}\ie4uinit.exe"; Parameters: "-show"; Flags: runhidden skipifdoesntexist
Filename: "{sys}\wscript.exe"; Parameters: """{app}\suite\iniciar_suite.vbs"""; Description: "Abrir a Suíte Angerô"; Flags: nowait postinstall skipifsilent
