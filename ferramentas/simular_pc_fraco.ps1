<#
  Simula um PC fraco para testar os programas da Suíte Angerô.
  Abre o programa dentro de um Job Object do Windows que limita CPU (%), núcleos e memória,
  rola as páginas e mede: tempo até a janela aparecer, travamentos ("Não está respondendo"),
  pico de CPU e de memória. Não precisa de admin.

  Exemplo:
    .\simular_pc_fraco.ps1 -Arquivo ficha.pdf -Nucleos 1 -CpuPorcento 4 -MemoriaMB 1024
    .\simular_pc_fraco.ps1 -Arquivo ficha.pdf -Renderizador gl
#>
param(
    [string]$Programa = (Get-ChildItem "$env:LOCALAPPDATA\Programs\Suite Angero\PDF*\pdf-angero.exe" | Select-Object -First 1).FullName,
    [Parameter(Mandatory)][string]$Arquivo,
    [int]$Nucleos = 0,          # 0 = todos
    [int]$CpuPorcento = 0,      # teto de CPU da máquina inteira (1-100); 0 = sem teto
    [int]$MemoriaMB = 0,        # 0 = sem limite
    [ValidateSet('auto', 'wgpu', 'gl')][string]$Renderizador = 'auto',
    [int]$Segundos = 40,
    [ValidateSet('', 'celeron')][string]$Perfil = '',
    [string]$Nome = 'teste'
)

Add-Type -TypeDefinition @'
using System; using System.Runtime.InteropServices;
public static class PcFraco {
    [DllImport("kernel32")] public static extern IntPtr CreateJobObject(IntPtr a, string n);
    [DllImport("kernel32")] public static extern bool AssignProcessToJobObject(IntPtr j, IntPtr p);
    [DllImport("kernel32")] public static extern bool SetInformationJobObject(IntPtr j, int c, IntPtr i, int l);
    [DllImport("kernel32")] public static extern IntPtr OpenProcess(int a, bool i, int pid);
    [DllImport("user32")] public static extern bool IsHungAppWindow(IntPtr h);
    [DllImport("user32")] public static extern bool PostMessage(IntPtr h, int m, IntPtr w, IntPtr l);
    [DllImport("user32")] public static extern bool SetForegroundWindow(IntPtr h);
    [DllImport("user32")] public static extern bool GetWindowRect(IntPtr h, out RECT r);
    public struct RECT { public int L, T, R, B; }

    // Amostra a cada 200 ms, em paralelo: "Não está respondendo" (como o Windows decide) e memória.
    public class Monitor {
        public IntPtr Janela; public long TravadoMs, MaiorTravadaMs, PicoMem;
        volatile bool parar; System.Threading.Thread t;
        public Monitor(System.Diagnostics.Process p) {
            t = new System.Threading.Thread(() => {
                long seq = 0;
                while (!parar) {
                    try {
                        if (p.HasExited) break;
                        p.Refresh(); PicoMem = Math.Max(PicoMem, p.WorkingSet64);
                        if (Janela != IntPtr.Zero && IsHungAppWindow(Janela)) { TravadoMs += 200; seq += 200; MaiorTravadaMs = Math.Max(MaiorTravadaMs, seq); } else seq = 0;
                    } catch { }
                    System.Threading.Thread.Sleep(200);
                }
            });
            t.IsBackground = true; t.Start();
        }
        public void Parar() { parar = true; t.Join(1000); }
    }

    public static IntPtr Criar(long afinidade, int cpuPct, long memBytes) {
        IntPtr job = CreateJobObject(IntPtr.Zero, null);
        // JOBOBJECT_EXTENDED_LIMIT_INFORMATION (classe 9): afinidade + memória por processo
        int tam = 144; IntPtr p = Marshal.AllocHGlobal(tam);
        for (int i = 0; i < tam; i++) Marshal.WriteByte(p, i, 0);
        int flags = 0;
        if (afinidade != 0) { flags |= 0x10; Marshal.WriteIntPtr(p, 48, new IntPtr(afinidade)); }
        if (memBytes != 0) { flags |= 0x100; Marshal.WriteIntPtr(p, 112, new IntPtr(memBytes)); }
        Marshal.WriteInt32(p, 16, flags);
        if (flags != 0 && !SetInformationJobObject(job, 9, p, tam)) throw new Exception("limites: " + Marshal.GetLastWin32Error());
        // JOBOBJECT_CPU_RATE_CONTROL_INFORMATION (classe 15): teto rígido de CPU
        if (cpuPct > 0) {
            IntPtr c = Marshal.AllocHGlobal(8);
            Marshal.WriteInt32(c, 0, 0x1 | 0x4);      // ENABLE | HARD_CAP
            Marshal.WriteInt32(c, 4, cpuPct * 100);   // em centésimos de %
            if (!SetInformationJobObject(job, 15, c, 8)) throw new Exception("cpu: " + Marshal.GetLastWin32Error());
        }
        return job;
    }
}
'@

$ErrorActionPreference = 'Stop'
if (-not $Programa -or -not (Test-Path $Programa)) { throw "Programa não encontrado: $Programa" }
if (-not (Test-Path $Arquivo)) { throw "Arquivo não encontrado: $Arquivo" }
$Arquivo = (Resolve-Path $Arquivo).Path
$exeNome = [IO.Path]::GetFileNameWithoutExtension($Programa)
Get-Process $exeNome -ErrorAction SilentlyContinue | Stop-Process -Force
Start-Sleep -Milliseconds 500

# Celeron/Core 2 Duo com 4 GB: 2 núcleos com ~1/2 núcleo atual de força no total; ~1,5 GB livre p/ o programa
if ($Perfil -eq 'celeron') { $Nucleos = 2; $CpuPorcento = [math]::Max(1, [int](50 / [Environment]::ProcessorCount)); $MemoriaMB = 1500 }
$afin = if ($Nucleos -gt 0) { [long]([math]::Pow(2, $Nucleos) - 1) } else { 0 }
$job = [PcFraco]::Criar($afin, $CpuPorcento, [long]$MemoriaMB * 1MB)

# --control: canal de automação do próprio programa (JSON-RPC por linha, só em 127.0.0.1, com token)
$ctl = Join-Path $env:TEMP "pcfraco-ctl-$PID.json"; Remove-Item $ctl -ErrorAction SilentlyContinue
$psi = New-Object Diagnostics.ProcessStartInfo $Programa, "--control `"$ctl`" `"$Arquivo`""
$psi.UseShellExecute = $false
if ($Renderizador -ne 'auto') { $psi.EnvironmentVariables['PDFCRAFT_RENDERER'] = $Renderizador }
$relogio = [Diagnostics.Stopwatch]::StartNew()
$proc = [Diagnostics.Process]::Start($psi)
$h = [PcFraco]::OpenProcess(0x1F0FFF, $false, $proc.Id)
[void][PcFraco]::AssignProcessToJobObject($job, $h)
$mon = New-Object PcFraco+Monitor $proc

function Resumo($obs) {
    $mon.Parar()
    [pscustomobject]@{
        Cenario            = $Nome
        Limites            = "nucleos=$(if($Nucleos){$Nucleos}else{'todos'}) cpu=$(if($CpuPorcento){"$CpuPorcento%"}else{'livre'}) mem=$(if($MemoriaMB){"$MemoriaMB MB"}else{'livre'}) render=$Renderizador"
        JanelaAbriu_s      = $script:tJanela
        PdfPronto_s        = $script:tPronto
        PaginaMedia_s      = $script:media
        PaginaPior_s       = $script:pior
        NaoRespondeu_s     = [math]::Round($mon.TravadoMs / 1000, 1)
        MaiorTravada_s     = [math]::Round($mon.MaiorTravadaMs / 1000, 1)
        PicoMemoria_MB     = [math]::Round($mon.PicoMem / 1MB)
        ErrosPagina        = $script:erros
        Observacao         = $obs
    }
    if (-not $proc.HasExited) { Stop-Process -Id $proc.Id -Force }
    Remove-Item $ctl -ErrorAction SilentlyContinue
}
$tJanela = $null; $tPronto = $null; $media = $null; $pior = $null; $erros = 0; $onde = 'abertura'; $piorDt = 0; $piorOnde = ''

# Espera a janela e o canal de controle
while (-not $proc.HasExited -and $relogio.Elapsed.TotalSeconds -lt $Segundos) {
    $proc.Refresh()
    if (-not $tJanela -and $proc.MainWindowHandle -ne [IntPtr]::Zero) { $tJanela = [math]::Round($relogio.Elapsed.TotalSeconds, 1); $mon.Janela = $proc.MainWindowHandle }
    if ($tJanela -and (Test-Path $ctl)) { break }
    Start-Sleep -Milliseconds 100
}
if ($proc.HasExited) { return Resumo "o programa fechou sozinho (código $($proc.ExitCode))" }
if (-not $tJanela) { return Resumo "a janela não abriu em $Segundos s" }

$c = Get-Content $ctl -Raw | ConvertFrom-Json
$tcp = New-Object Net.Sockets.TcpClient '127.0.0.1', $c.port
$tcp.ReceiveTimeout = $Segundos * 1000
$fluxo = $tcp.GetStream(); $wr = New-Object IO.StreamWriter $fluxo; $wr.AutoFlush = $true; $rd = New-Object IO.StreamReader $fluxo
function Rpc($metodo, $params) {
    $wr.WriteLine((@{ jsonrpc = '2.0'; id = 1; method = $metodo; params = $params } | ConvertTo-Json -Compress -Depth 5))
    $resp = $rd.ReadLine() | ConvertFrom-Json
    if ($resp.error) { throw "$metodo : $($resp.error.message)" }
    $resp.result
}
# Espera desenhar: nenhuma página pendente; devolve o estado
function EsperarDesenho {
    $limite = $relogio.Elapsed.TotalSeconds + $Segundos
    do {
        $st = Rpc 'ui.state' @{}
        if ($st.active -and $st.active.raster_memory.pending_requests -eq 0 -and $st.pending_opens.Count -eq 0) { return $st }
        Start-Sleep -Milliseconds 50
    } while ($relogio.Elapsed.TotalSeconds -lt $limite)
    throw "a página não terminou de desenhar em $Segundos s"
}

try {
    [void](Rpc 'auth' @{ token = $c.token })
    $st = EsperarDesenho
    $tPronto = [math]::Round($relogio.Elapsed.TotalSeconds, 1)
    $paginas = ($st.documents | Where-Object active).pages
    $tempos = @()
    foreach ($zoom in 100, 300) {
        [void](Rpc 'ui.set' @{ key = 'zoom'; value = "$zoom" })
        for ($pg = 1; $pg -le $paginas; $pg++) {
            $t0 = $relogio.Elapsed.TotalSeconds
            [void](Rpc 'ui.set' @{ key = 'page'; value = "$pg" })
            $script:onde = "página $pg, zoom $zoom%"
            $st = EsperarDesenho
            $dt = $relogio.Elapsed.TotalSeconds - $t0
            $tempos += $dt
            if ($dt -gt $script:piorDt) { $script:piorDt = $dt; $script:piorOnde = $script:onde }
            $erros = [math]::Max($erros, @($st.active.page_errors).Count)
        }
    }
    $media = [math]::Round(($tempos | Measure-Object -Average).Average, 2)
    $pior = [math]::Round(($tempos | Measure-Object -Maximum).Maximum, 2)
    $tcp.Close()
    Resumo "ok: $paginas páginas x zoom 100% e 300%; mais lenta: $piorOnde"
} catch {
    Resumo "PROBLEMA em $($script:onde): $($_.Exception.Message)$(if ($proc.HasExited) { ' (o programa fechou)' })"
}

