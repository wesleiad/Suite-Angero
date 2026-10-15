# Assistente Angerô — configuração (TI)

O usuário não vê nem altera a chave da IA. Ela é configurada pelo TI, por computador:

1. **Por GPO (todos os computadores):** Configuração do Computador › Preferências › Configurações do Windows › Registro ›
   Novo item: `HKEY_LOCAL_MACHINE\Software\Grupo Angero\Suite Angero\Assistente`, valor **GeminiChave** (REG_SZ) = a chave.
   Opcional: **GeminiModelo** (ex.: `gemini-3.8-flash`).
2. **Num computador só:** PowerShell como administrador:
   `instalador\configurar_ia.ps1 -Chave "AQ.xxxxx"`

A chave é criada em aistudio.google.com › Get API key (plano gratuito). Ela **nunca** vai para o GitHub.
Se o Google aposentar o modelo, a Suíte troca sozinha para o substituto indicado pelo Google.
Na tela ⚙ Configurações da Suíte aparece só "Assistente configurado pelo TI" ou "fale com o TI".
