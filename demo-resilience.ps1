# ============================================================
#  DEMO SCRIPT - Resilience & Async Features
#  Library Microservice System
#  Jalankan: .\demo-resilience.ps1
# ============================================================

$GATEWAY = "http://localhost:8080"
$script:TOKEN = ""

function Write-Header($text) {
    Write-Host ""
    Write-Host "==============================================" -ForegroundColor Cyan
    Write-Host "  $text" -ForegroundColor Cyan
    Write-Host "==============================================" -ForegroundColor Cyan
}

function Write-Step($num, $text) {
    Write-Host ""
    Write-Host "  [$num] $text" -ForegroundColor Yellow
}

function Write-OK($text)   { Write-Host "      OK  $text" -ForegroundColor Green }
function Write-ERR($text)  { Write-Host "      ERR $text" -ForegroundColor Red }
function Write-INFO($text) { Write-Host "      ... $text" -ForegroundColor Gray }

function Pause-Demo($msg) {
    Write-Host ""
    Write-Host "  >> $msg" -ForegroundColor Magenta
    Read-Host "     Tekan ENTER untuk lanjut"
}

# ────────────────────────────────────────────────────────────
function Get-Token {
    Write-Header "LOGIN - Ambil Access Token"
    $username = Read-Host "  Username"
    $password = Read-Host "  Password"

    $body = @{ username = $username; password = $password } | ConvertTo-Json
    try {
        $res = Invoke-RestMethod -Uri "$GATEWAY/auth/login" `
            -Method POST -Body $body -ContentType "application/json"
        $script:TOKEN = $res.access_token
        Write-OK "Login berhasil. Token didapat."
    } catch {
        Write-ERR "Login gagal: $_"
        exit 1
    }
}

# ────────────────────────────────────────────────────────────
function Show-CircuitBreakerStatus {
    try {
        $res = Invoke-RestMethod -Uri "$GATEWAY/admin/circuit-breakers" -Method GET
        Write-Host ""
        Write-Host "  Circuit Breaker Status:" -ForegroundColor White
        foreach ($key in $res.PSObject.Properties.Name) {
            $cb    = $res.$key
            $state = $cb.state
            $color = switch ($state) {
                "closed"    { "Green" }
                "open"      { "Red" }
                "half_open" { "Yellow" }
                default     { "White" }
            }
            $line = "    {0,-20} state={1,-10} failures={2}/{3}" -f $cb.name, $state, $cb.failures, $cb.fail_max
            Write-Host $line -ForegroundColor $color
        }
    } catch {
        Write-ERR "Tidak bisa ambil status: $_"
    }
}

# ────────────────────────────────────────────────────────────
function Demo-CircuitBreaker {
    Write-Header "DEMO 1 - Circuit Breaker"

    Write-Step 1 "Cek status awal circuit breaker (semua harus CLOSED)"
    Show-CircuitBreakerStatus

    Pause-Demo "Sekarang kita matikan Book Service"

    Write-Step 2 "Stop book-service container"
    docker compose stop book-service
    Write-OK "book-service dihentikan."
    Start-Sleep -Seconds 2

    Pause-Demo "Kirim 6 request ke /books - circuit breaker terbuka setelah 5 failure"

    Write-Step 3 "Kirim 6 request ke GET /books"
    $headers = @{ Authorization = "Bearer $($script:TOKEN)" }
    for ($i = 1; $i -le 6; $i++) {
        $sw = [System.Diagnostics.Stopwatch]::StartNew()
        try {
            Invoke-RestMethod -Uri "$GATEWAY/books" -Headers $headers -Method GET | Out-Null
            $sw.Stop()
            Write-OK "Request $i - 200 OK ($($sw.ElapsedMilliseconds)ms)"
        } catch {
            $sw.Stop()
            $code = $_.Exception.Response.StatusCode.value__
            $ms   = $sw.ElapsedMilliseconds
            Write-ERR "Request $i - HTTP $code ($ms ms)"
        }
    }

    Write-Step 4 "Cek status circuit breaker - book-service harus OPEN"
    Show-CircuitBreakerStatus

    Pause-Demo "Kirim 1 request lagi - harusnya INSTAN reject (bukan nunggu timeout)"

    Write-Step 5 "1 request saat circuit OPEN - langsung ditolak gateway"
    $sw = [System.Diagnostics.Stopwatch]::StartNew()
    try {
        Invoke-RestMethod -Uri "$GATEWAY/books" -Headers $headers -Method GET | Out-Null
        $sw.Stop()
        Write-OK "200 OK ($($sw.ElapsedMilliseconds)ms)"
    } catch {
        $sw.Stop()
        $code = $_.Exception.Response.StatusCode.value__
        $ms   = $sw.ElapsedMilliseconds
        Write-ERR "HTTP $code - ditolak dalam $ms ms (circuit open, tidak nyoba connect)"
    }

    Write-INFO "Tunggu 30 detik untuk HALF_OPEN..."
    for ($i = 30; $i -gt 0; $i--) {
        Write-Host "`r      Menunggu $i detik...   " -NoNewline
        Start-Sleep -Seconds 1
    }
    Write-Host ""

    Write-Step 6 "Cek status - harusnya HALF_OPEN sekarang"
    Show-CircuitBreakerStatus

    Pause-Demo "Nyalakan kembali book-service, lalu kirim 1 request untuk recovery"

    Write-Step 7 "Start book-service"
    docker compose start book-service
    Write-OK "book-service dinyalakan."
    Start-Sleep -Seconds 3

    Write-Step 8 "Kirim 1 request - kalau sukses, circuit kembali CLOSED"
    $sw = [System.Diagnostics.Stopwatch]::StartNew()
    try {
        Invoke-RestMethod -Uri "$GATEWAY/books" -Headers $headers -Method GET | Out-Null
        $sw.Stop()
        Write-OK "200 OK ($($sw.ElapsedMilliseconds)ms) - circuit menutup kembali"
    } catch {
        $sw.Stop()
        $code = $_.Exception.Response.StatusCode.value__
        $ms   = $sw.ElapsedMilliseconds
        Write-ERR "HTTP $code ($ms ms)"
    }

    Write-Step 9 "Status akhir circuit breaker"
    Show-CircuitBreakerStatus
}

# ────────────────────────────────────────────────────────────
function Demo-Async {
    Write-Header "DEMO 2 - Async Concurrent Requests"

    Write-Step 1 "Kirim 10 request ke /health secara BERSAMAAN"
    Write-INFO "Kalau async: semua selesai hampir bersamaan"
    Write-INFO "Kalau sync : request ke-10 nunggu ke-1 dulu"

    $sw = [System.Diagnostics.Stopwatch]::StartNew()
    $jobs = 1..10 | ForEach-Object {
        $idx = $_
        Start-Job -ScriptBlock {
            param($url, $i)
            $s = [System.Diagnostics.Stopwatch]::StartNew()
            try {
                Invoke-RestMethod -Uri $url -Method GET | Out-Null
                $s.Stop()
                "Request $i selesai: $($s.ElapsedMilliseconds)ms - OK"
            } catch {
                $s.Stop()
                "Request $i selesai: $($s.ElapsedMilliseconds)ms - ERR"
            }
        } -ArgumentList "$GATEWAY/health", $idx
    }

    $results = $jobs | Wait-Job | Receive-Job
    $sw.Stop()
    $jobs | Remove-Job

    $results | Sort-Object | ForEach-Object { Write-Host "    $_" -ForegroundColor Green }
    Write-Host ""
    $total = $sw.ElapsedMilliseconds
    Write-OK "Total waktu 10 request paralel: $total ms"
    Write-INFO "(Kalau sync, total = jumlah waktu semua request satu per satu)"
}

# ────────────────────────────────────────────────────────────
function Demo-GracefulDegradation {
    Write-Header "DEMO 3 - Graceful Degradation (Redis Down)"

    Write-Step 1 "Pastikan login berfungsi normal saat Redis aktif"
    $un   = Read-Host "  Username (akun yang valid)"
    $pw   = Read-Host "  Password"
    $body = @{ username = $un; password = $pw } | ConvertTo-Json

    try {
        Invoke-RestMethod -Uri "$GATEWAY/auth/login" -Method POST `
            -Body $body -ContentType "application/json" | Out-Null
        Write-OK "Login berhasil - Redis aktif, event auth.user.logged_in dipublish"
    } catch {
        $code = $_.Exception.Response.StatusCode.value__
        Write-ERR "HTTP $code"
    }

    Pause-Demo "Matikan Redis sekarang - lalu tekan ENTER"

    Write-Step 2 "Stop Redis"
    docker compose stop redis
    Write-OK "Redis dihentikan."
    Start-Sleep -Seconds 2

    Write-Step 3 "Coba login lagi - Auth Service harus TETAP berjalan"
    try {
        Invoke-RestMethod -Uri "$GATEWAY/auth/login" -Method POST `
            -Body $body -ContentType "application/json" | Out-Null
        Write-OK "Login TETAP berhasil meski Redis mati (graceful degradation)"
        Write-INFO "Cek log: docker compose logs auth-service --tail 10"
    } catch {
        $code = $_.Exception.Response.StatusCode.value__
        if ($code -eq 401) {
            Write-OK "Auth Service TETAP merespons (401 = credential, bukan crash service)"
            Write-INFO "Service jalan normal, hanya event publish yang di-skip"
        } else {
            Write-ERR "HTTP $code - service mungkin crash"
        }
    }

    Write-Step 4 "Lihat log Auth Service untuk konfirmasi"
    docker compose logs auth-service --tail 15

    Write-Step 5 "Nyalakan Redis kembali"
    docker compose start redis
    Write-OK "Redis dinyalakan."
}

# ────────────────────────────────────────────────────────────
#  MAIN MENU
# ────────────────────────────────────────────────────────────
Write-Host ""
Write-Host "  Library Microservice - Demo Resilience & Async" -ForegroundColor Cyan
Write-Host "  ================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "  Pilih demo:" -ForegroundColor White
Write-Host "    [1] Circuit Breaker (matikan service, lihat state change)" -ForegroundColor White
Write-Host "    [2] Async Concurrent Requests" -ForegroundColor White
Write-Host "    [3] Graceful Degradation (Redis down)" -ForegroundColor White
Write-Host "    [A] Jalankan semua" -ForegroundColor White
Write-Host ""

$choice = Read-Host "  Pilihan"

if ($choice -in @("1", "A", "a")) {
    Get-Token
}

switch ($choice.ToUpper()) {
    "1" { Demo-CircuitBreaker }
    "2" { Demo-Async }
    "3" { Demo-GracefulDegradation }
    "A" {
        Demo-CircuitBreaker
        Demo-Async
        Demo-GracefulDegradation
    }
    default { Write-ERR "Pilihan tidak valid." }
}

Write-Host ""
Write-Host "  Demo selesai." -ForegroundColor Cyan
Write-Host ""
