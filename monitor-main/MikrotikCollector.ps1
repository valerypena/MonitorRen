
# MIKROTIK COLLECTOR (PERSISTENT REAL-TIME)
# - Maintains connection open (Faster, Low Overhead)
# - Reconnects automatically on error
# - Polls every 1 second

$MkIp = "10.24.0.1"
$MkPort = 8728
$MkUser = "Ejgonzalez"
$MkPass = "Sara28031610"
$ApiUrl = "http://localhost/ren_monitor/api_ingest.php"
$PingTarget = "1.1.1.1" # Cloudflare DNS (Alt Target)

# --- HELPER FUNCTIONS ---
function Get-Hash($bytes) {
    try {
        $md5 = [System.Security.Cryptography.MD5]::Create()
        $hash = $md5.ComputeHash($bytes)
        return [BitConverter]::ToString($hash).Replace("-", "").ToLower()
    }
    catch { return "" }
}

function HexToBytes($hex) {
    try {
        $bytes = @()
        for ($i = 0; $i -lt $hex.Length; $i += 2) {
            $bytes += [Convert]::ToByte($hex.Substring($i, 2), 16)
        }
        return $bytes
    }
    catch { return @() }
}

function Send-Word($stream, $command) {
    $bytes = [System.Text.Encoding]::ASCII.GetBytes($command)
    $len = $bytes.Length
    if ($len -lt 0x80) { $stream.WriteByte($len) }
    else {
        $stream.WriteByte([byte](0x80 -bor ($len -shr 8)))
        $stream.WriteByte([byte]($len -band 0xFF))
    }
    $stream.Write($bytes, 0, $len)
}

function Read-Word($stream) {
    $b = $stream.ReadByte()
    if ($b -eq -1) { throw "Disconnect" }
    $len = $b
    if (($b -band 0x80) -ne 0) {
        $len = (($b -band 0x7F) -shl 8) + $stream.ReadByte()
    }
    $buffer = New-Object byte[] $len
    $read = 0
    while ($read -lt $len) {
        $read += $stream.Read($buffer, $read, $len - $read)
    }
    return [System.Text.Encoding]::ASCII.GetString($buffer)
}

function Read-Sentence($stream) {
    $s = @{}
    while ($true) {
        $word = Read-Word $stream
        if ([string]::IsNullOrEmpty($word)) { return $s }
        
        if ($word -eq "!done") { $s["!done"] = $true }
        elseif ($word -eq "!re") { $s["!re"] = $true }
        elseif ($word -eq "!trap") { $s["!trap"] = $true; $s["message"] = "TRAP" }
        elseif ($word -eq "!fatal") { throw "FATAL ERROR FROM ROUTER" }
        elseif ($word.Contains("=")) { 
            $parts = $word.Split("=", 3)
            if ($parts.Length -ge 3) { $s[$parts[1]] = $parts[2] }
        }
    }
}

function Invoke-Login($stream) {
    Send-Word $stream "/login"; Send-Word $stream "=name=$MkUser"; Send-Word $stream "=password=$MkPass"; Send-Word $stream ""
    $res = Read-Sentence $stream
    if ($res["ret"]) {
        $challengeHex = $res["ret"]
        $passBytes = [System.Text.Encoding]::ASCII.GetBytes($MkPass)
        $chalBytes = HexToBytes $challengeHex
        $zero = [byte]0
        $toHash = [byte[]](@($zero) + $passBytes + $chalBytes)
        $responseHash = Get-Hash $toHash
        Send-Word $stream "/login"; Send-Word $stream "=name=$MkUser"; Send-Word $stream "=response=00$responseHash"; Send-Word $stream ""
        $res2 = Read-Sentence $stream
        if ($res2["!trap"]) { throw "Login Challenge Failed" }
    }
    elseif ($res["!trap"]) { throw "Login Failed" }
}

# --- MAIN ---
Write-Host "Iniciando Colector (MODO PERSISTENTE 1s)..." -ForegroundColor Cyan

if (-not $global:Ctx) {
    $global:Ctx = @{ PrevTime = 0; W1Rx = 0; W1Tx = 0; W2Rx = 0; W2Tx = 0; PrevW1Rx = 0; PrevW1Tx = 0; PrevW2Rx = 0; PrevW2Tx = 0; PrevDrops = 0; LoopCount = 0; SecretMap = @{} }
}

while ($true) {
    $client = $null
    $stream = $null
    try {
        # CONNECT ONCE
        Write-Host "Conectando al Mikrotik..." -ForegroundColor Yellow
        $client = New-Object System.Net.Sockets.TcpClient
        $client.Connect($MkIp, $MkPort)
        $client.ReceiveTimeout = 5000 # 5 Seconds Timeout (Prevents Hanging)
        $stream = $client.GetStream()
        Invoke-Login $stream
        Write-Host "Conectado. Iniciando bucle de datos..." -ForegroundColor Green
        
        # LOOP FOREVER (Until error)
        while ($true) {
            $loopStart = Get-Date

            # --- FETCH VARS ---
            $cpu = 0; $memFree = 0; $memTotal = 0; $hddFree = 0; $hddTotal = 0; $uptime = ""
            $temp = 0; $volt = 0; $dhcpCount = 0
            $vpnTotal = 0; $vpnL2tp = 0; $vpnOvpn = 0; $vpnPptp = 0; $vpnSstp = 0
            $rawDrops = 0; $sfpPower = 0; $logMsg = ""; $queueCount = 0
            $sfpInterface = ""

            # -- SFP (Find Interface Loop Removed) --
            # Logic moved to startup (although we are not using SFP anymore per user request)

            # -- RESOURCES --
            Send-Word $stream "/system/resource/print"; Send-Word $stream ""
            while ($true) { 
                $r = Read-Sentence $stream
                if ($r["cpu-load"]) { $cpu = $r["cpu-load"]; $memFree = $r["free-memory"]; $memTotal = $r["total-memory"]; $hddFree = $r["free-hdd-space"]; $hddTotal = $r["total-hdd-space"]; $uptime = $r["uptime"] }
                if ($r["!done"]) { break } 
            }

            # -- HEALTH --
            Send-Word $stream "/system/health/print"; Send-Word $stream ""
            while ($true) { $r = Read-Sentence $stream; if ($r["temperature"]) { $temp = $r["temperature"] }; if ($r["voltage"]) { $volt = $r["voltage"] }; if ($r["!done"]) { break } }

            # -- DHCP --
            Send-Word $stream "/ip/dhcp-server/lease/print"; Send-Word $stream "=count-only="; Send-Word $stream ""
            while ($true) { $r = Read-Sentence $stream; if ($r["ret"]) { $dhcpCount = $r["ret"] }; if ($r["!done"]) { break } }

            # -- VPN BREAKDOWN (Profile Based) --
            # 1. Update Secret Map (User -> Profile) periodically (e.g. every 60 loops)
            if ($global:Ctx.LoopCount % 60 -eq 0) {
                $global:Ctx.SecretMap = @{}
                Send-Word $stream "/ppp/secret/print"; Send-Word $stream ""
                while ($true) {
                    $r = Read-Sentence $stream
                    if ($r["name"] -and $r["profile"]) { $global:Ctx.SecretMap[$r["name"]] = $r["profile"] }
                    if ($r["!done"]) { break }
                }
                Write-Host "DEBUG: Secrets Cached: $($global:Ctx.SecretMap.Count)" -ForegroundColor Gray
            }
            $global:Ctx.LoopCount++

            # 2. Count Active Users per Profile
            $vpnTotal = 0; $vpnL2tp = 0; $vpnOvpn = 0; $vpnPptp = 0; $vpnSstp = 0
            $ProfileCounts = @{}

            Send-Word $stream "/ppp/active/print"; Send-Word $stream ""
            while ($true) {
                $r = Read-Sentence $stream
                if ($r["name"]) { 
                    $vpnTotal++
                    
                    # Protocol Stats
                    if ($r["service"] -match "l2tp") { $vpnL2tp++ } 
                    elseif ($r["service"] -match "ovpn") { $vpnOvpn++ } 
                    elseif ($r["service"] -match "sstp") { $vpnSstp++ } 
                    else { $vpnPptp++ }
                    
                    # Profile Mapping
                    $user = $r["name"]
                    $prof = "Unknown"
                    if ($global:Ctx.SecretMap.ContainsKey($user)) {
                        $prof = $global:Ctx.SecretMap[$user]
                    }
                    
                    if ($ProfileCounts.ContainsKey($prof)) { $ProfileCounts[$prof]++ }
                    else { $ProfileCounts[$prof] = 1 }
                }
                if ($r["!done"]) { break }
            }


            # -- QUEUES --


            # -- LOGS --
            Send-Word $stream "/log/print"; Send-Word $stream "=limit=3"; Send-Word $stream ""
            while ($true) { 
                $r = Read-Sentence $stream; 
                if ($r["message"] -and $r["topics"] -match "error|critical") { $logMsg = "$($r['time']) $($r['message'])" }
                if ($r["!done"]) { break } 
            }

            # -- SFP POWER REMOVED --

            # -- FIREWALL DROPS (Real Threat Intel) --
            $fwDrops = 0
            Send-Word $stream "/ip/firewall/filter/print"; Send-Word $stream "=stats="; Send-Word $stream "?action=drop"; Send-Word $stream ""
            while ($true) {
                $r = Read-Sentence $stream
                if ($r["packets"]) { $fwDrops += [long]$r["packets"] }
                if ($r["!done"]) { break }
            }

            # -- TRAFFIC & TOP SOURCES --
            # Reusing the single Interface Print command for everything to be efficient
            $c_w1r = 0; $c_w1t = 0; $c_w2r = 0; $c_w2t = 0
            
            # Global specific WANs
            # Calculate Rates for ALL interfaces
            if (-not $global:Ctx.PrevIfaces) { $global:Ctx.PrevIfaces = @{} }
            
            $iList = @()
            $secs = 1; if ($global:Ctx.LastTrafficTime) { $secs = ((Get-Date) - $global:Ctx.LastTrafficTime).TotalSeconds }
            if ($secs -eq 0) { $secs = 1 }
            $global:Ctx.LastTrafficTime = Get-Date

            Send-Word $stream "/interface/print"; Send-Word $stream "=stats="; Send-Word $stream ""
            while ($true) {
                $r = Read-Sentence $stream
                
                if ($r["name"]) {
                    $name = $r["name"]
                    $currRx = 0; if ($r["rx-byte"]) { $currRx = [long]$r["rx-byte"] }
                    
                    # WAN LOGIC (Keep existing)
                    if ($name -eq "v_2689") { $c_w1r = $currRx; if ($r["tx-byte"]) { $c_w1t = [long]$r["tx-byte"] }; if ($r["rx-drop"]) { $rawDrops += [int]$r["rx-drop"] } }
                    elseif ($name -eq "WAN2-ether3") { $c_w2r = $currRx; if ($r["tx-byte"]) { $c_w2t = [long]$r["tx-byte"] } }

                    # UNIVERSAL RATE CALC
                    if ($currRx -gt 0) {
                        $prevRx = 0
                        if ($global:Ctx.PrevIfaces.ContainsKey($name)) { $prevRx = $global:Ctx.PrevIfaces[$name] }
                        
                        # Calc Delta
                        if ($prevRx -gt 0 -and $currRx -ge $prevRx) {
                            $bits = ($currRx - $prevRx) * 8
                            $bps = $bits / $secs
                            
                            # Add to candidate list if significant (>1kbps)
                            if ($bps -gt 1000) {
                                $iList += @{ Name = $name; Rate = $bps }
                            }
                        }
                        # Update Prev
                        $global:Ctx.PrevIfaces[$name] = $currRx
                    }
                }
                
                if ($r["!done"]) { break }
            }

            # Sort -> Top 3 Interfaces
            $topQueues = $iList | Sort-Object Rate -Descending | Select-Object -First 3
            if (-not $topQueues) { $topQueues = @() }

            # -- PING / LATENCY (Restored & Improved) --
            Send-Word $stream "/ping"; Send-Word $stream "=address=$PingTarget"; Send-Word $stream "=count=1"; Send-Word $stream ""
            while ($true) {
                $r = Read-Sentence $stream
                
                if ($r["avg-rtt"]) { 
                    # Parse "10ms" or "0.4ms"
                    $clean = $r["avg-rtt"] -replace "ms|s", "" 
                    if ($clean) { $pingMs = $clean -as [double] }
                }
                
                if ($r["packet-loss"]) { 
                    $clean = $r["packet-loss"] -replace "%", ""
                    if ($clean) { $pingLoss = $clean -as [int] }
                }
                
                # Handle Timeout explicitly
                if ($r["status"] -eq "timeout") { 
                    $pingLoss = 100 
                    $pingMs = 0 
                }

                if ($r["!done"]) { break }
            }

            # --- CALC SPEED ---
            $now = Get-Date
            if (-not $global:Ctx.PrevTime) { $global:Ctx.PrevTime = $now }
            else {
                $secs = ($now - $global:Ctx.PrevTime).TotalSeconds
                if ($secs -lt 0.5) { $secs = 0.5 } # Prevent div by zero
                
                # W1
                if ($c_w1r -gt $global:Ctx.PrevW1Rx) { $global:Ctx.W1Rx = ($c_w1r - $global:Ctx.PrevW1Rx) * 8 / $secs } else { $global:Ctx.W1Rx = 0 }
                if ($c_w1r -gt 0 -and $global:Ctx.PrevW1Rx -eq 0) { $global:Ctx.W1Rx = 0 }
                # W2
                if ($c_w2r -gt $global:Ctx.PrevW2Rx) { $global:Ctx.W2Rx = ($c_w2r - $global:Ctx.PrevW2Rx) * 8 / $secs } else { $global:Ctx.W2Rx = 0 }
                
                $global:Ctx.PrevTime = $now
            }
            $global:Ctx.PrevW1Rx = $c_w1r; $global:Ctx.PrevW1Tx = $c_w1t; $global:Ctx.PrevW2Rx = $c_w2r; $global:Ctx.PrevW2Tx = $c_w2t

            # Calc Drops
            $dDrops = 0; if ($rawDrops -gt $global:Ctx.PrevDrops) { $dDrops = $rawDrops - $global:Ctx.PrevDrops }; $global:Ctx.PrevDrops = $rawDrops

            # --- POST ---
            $json = @{
                created_at = $now.ToString("yyyy-MM-dd HH:mm:ss");
                cpu_load = $cpu; free_memory = [long]$memFree; total_memory = [long]$memTotal;
                temperature = [int]$temp; voltage = [int]$volt; uptime = $uptime;
                vpn_count = [int]$vpnTotal; vpn_l2tp = [int]$vpnL2tp; vpn_ovpn = [int]$vpnOvpn; vpn_sstp = [int]$vpnSstp; vpn_pptp = [int]$vpnPptp;
                wan1_tx = [long]$global:Ctx.W1Tx; wan1_rx = [long]$global:Ctx.W1Rx; wan2_tx = [long]$global:Ctx.W2Tx; wan2_rx = [long]$global:Ctx.W2Rx;
                wan_drops = [int]$dDrops; sfp_rx_power = [double]$sfpPower; 
                dhcp_leases = [int]$dhcpCount; queue_count = [int]$queueCount; log_message = $logMsg;
                hdd_free = [long]$hddFree; hdd_total = [long]$hddTotal;
                ping_avg_ms = [double]$pingMs; ping_loss_percent = [int]$pingLoss;
                
                # New VPN Detail
                vpn_profiles_detail = $ProfileCounts;
                firewall_drops_total = [long]$fwDrops;
                
                # Top Consumers
                top_consumers = $topQueues
            } | ConvertTo-Json -Compress -Depth 10
            
            # DEBUG
            # Write-Host "JSON_PAYLOAD: $json" -ForegroundColor Cyan
            
            Invoke-RestMethod -Uri $ApiUrl -Method Post -Body $json -ContentType "application/json"
            
            # Log
            $w1kb = [math]::Round($global:Ctx.W1Rx / 1000, 0)
            Write-Host "[$($now.ToString('HH:mm:ss'))] SYNC | Claro: $w1kb Kbps | Ping: $pingMs ms" -ForegroundColor Green

            # --- SLEEP CORRECTED ---
            # Adjust sleep to aim for exactly 1s interval
            $elapsed = (Get-Date) - $loopStart
            $sleepMs = 1000 - $elapsed.TotalMilliseconds
            if ($sleepMs -gt 0) { Start-Sleep -Milliseconds $sleepMs }
        }

    }
    catch {
        Write-Host "ERROR: $($_.Exception.Message). Reconnecting in 2s..." -ForegroundColor Red
        if ($client) { $client.Close() }
        Start-Sleep -Seconds 2
    }
}
