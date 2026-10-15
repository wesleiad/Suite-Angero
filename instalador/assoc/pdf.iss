; gerado por gerar_associacoes.py: PDF - Angerô
#ifndef Cmd_pdf
  #define Cmd_pdf '""' + AppPasta_pdf + '\pdf-angero.exe"" ""%1""'
#endif
Root: HKCU; Subkey: "Software\Classes\SuiteAngero.pdf.pdf"; ValueType: string; ValueName: ""; ValueData: "Documento PDF"; Flags: uninsdeletekey
Root: HKCU; Subkey: "Software\Classes\SuiteAngero.pdf.pdf\DefaultIcon"; ValueType: string; ValueName: ""; ValueData: "{#AppPasta_pdf}\icone.ico"
Root: HKCU; Subkey: "Software\Classes\SuiteAngero.pdf.pdf\shell\open\command"; ValueType: string; ValueName: ""; ValueData: "{#Cmd_pdf}"
Root: HKCU; Subkey: "Software\Classes\.pdf\OpenWithProgids"; ValueType: string; ValueName: "SuiteAngero.pdf.pdf"; ValueData: ""; Flags: uninsdeletevalue
Root: HKCU; Subkey: "Software\Classes\.pdf"; ValueType: string; ValueName: ""; ValueData: "SuiteAngero.pdf.pdf"; Flags: uninsdeletevalue; Tasks: associar
