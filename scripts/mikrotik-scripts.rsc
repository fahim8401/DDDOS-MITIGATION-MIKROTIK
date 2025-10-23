# MikroTik RouterOS v7 DDoS Mitigation Scripts
# Import-safe configuration for DDoS protection
# 
# Usage: /import mikrotik-scripts.rsc
# 
# These scripts configure:
# - Firewall rules for DDoS protection
# - Address lists for blocking
# - Connection tracking settings
# - Rate limiting rules

# ============================================
# Configuration Variables
# ============================================
:local ddosBlockList "ddos_blocklist"
:local ddosWhitelist "ddos_whitelist"
:local logPrefix "DDoS-Protection"

# ============================================
# Create Address Lists
# ============================================
:log info "$logPrefix: Creating address lists..."

# DDoS blocklist (populated by monitoring application)
/ip firewall address-list
:if ([find list=$ddosBlockList] = "") do={
    add list=$ddosBlockList comment="DDoS Attack Sources - Auto-managed"
}

# Whitelist for trusted IPs
/ip firewall address-list
:if ([find list=$ddosWhitelist] = "") do={
    add list=$ddosWhitelist address=192.168.88.0/24 comment="Local Network"
    add list=$ddosWhitelist address=10.0.0.0/8 comment="Private Network"
}

# ============================================
# Connection Tracking Settings
# ============================================
:log info "$logPrefix: Configuring connection tracking..."

/ip settings
set tcp-syncookies=yes
set max-neighbor-entries=8192

/ip firewall connection tracking
set enabled=yes
set tcp-established-timeout=1h
set tcp-syn-sent-timeout=20s
set tcp-syn-received-timeout=20s
set tcp-fin-wait-timeout=20s
set tcp-time-wait-timeout=20s
set tcp-close-timeout=10s
set tcp-close-wait-timeout=20s
set udp-timeout=30s
set udp-stream-timeout=3m
set icmp-timeout=10s

# ============================================
# Firewall Filter Rules - DDoS Protection
# ============================================
:log info "$logPrefix: Creating firewall filter rules..."

/ip firewall filter

# Accept established and related connections
add chain=input connection-state=established,related action=accept \
    comment="Accept established/related"

# Accept connections from whitelist
add chain=input src-address-list=$ddosWhitelist action=accept \
    comment="Accept from whitelist"

# Drop connections from blocklist
add chain=input src-address-list=$ddosBlockList action=drop \
    comment="Drop DDoS sources"

# Protect against SYN flood
add chain=input protocol=tcp tcp-flags=syn connection-state=new \
    action=add-src-to-address-list address-list=syn_flooder \
    address-list-timeout=30s tcp-mss=0-535 \
    comment="Detect SYN flood (low MSS)"

add chain=input protocol=tcp src-address-list=syn_flooder \
    action=drop comment="Drop SYN flood"

# Protect against port scans
add chain=input protocol=tcp tcp-flags=fin,!syn,!rst,!psh,!ack,!urg \
    action=add-src-to-address-list address-list=port_scanner \
    address-list-timeout=1d comment="Detect port scan (FIN)"

add chain=input protocol=tcp tcp-flags=!fin,!syn,!rst,!psh,!ack,!urg \
    action=add-src-to-address-list address-list=port_scanner \
    address-list-timeout=1d comment="Detect port scan (NULL)"

add chain=input protocol=tcp tcp-flags=fin,syn \
    action=add-src-to-address-list address-list=port_scanner \
    address-list-timeout=1d comment="Detect port scan (FIN,SYN)"

add chain=input protocol=tcp tcp-flags=fin,rst \
    action=add-src-to-address-list address-list=port_scanner \
    address-list-timeout=1d comment="Detect port scan (FIN,RST)"

add chain=input src-address-list=port_scanner action=drop \
    comment="Drop port scanners"

# Protect against ICMP flood
add chain=input protocol=icmp icmp-options=8:0 limit=5,5:packet \
    action=accept comment="Allow limited ICMP ping"

add chain=input protocol=icmp action=drop \
    comment="Drop excessive ICMP"

# Protect against UDP flood
add chain=input protocol=udp connection-state=new \
    action=add-src-to-address-list address-list=udp_flooder \
    address-list-timeout=30s limit=50,5:packet \
    comment="Detect UDP flood"

add chain=input src-address-list=udp_flooder action=drop \
    comment="Drop UDP flood"

# ============================================
# Firewall RAW Rules - Early Drop
# ============================================
:log info "$logPrefix: Creating firewall RAW rules..."

/ip firewall raw

# Drop invalid packets
add chain=prerouting connection-state=invalid action=drop \
    comment="Drop invalid packets"

# Drop bad TCP flags
add chain=prerouting protocol=tcp tcp-flags=!fin,!syn,!rst,!ack \
    action=drop comment="Drop bad TCP flags"

# Drop from blocklist early
add chain=prerouting src-address-list=$ddosBlockList action=drop \
    comment="Early drop DDoS sources"

# ============================================
# Firewall Mangle Rules - Connection Marking
# ============================================
:log info "$logPrefix: Creating firewall mangle rules..."

/ip firewall mangle

# Mark new connections
add chain=prerouting connection-state=new action=mark-connection \
    new-connection-mark=new_conn passthrough=yes \
    comment="Mark new connections"

# Track connection rate per source
add chain=prerouting src-address-list=!$ddosWhitelist \
    connection-mark=new_conn action=add-src-to-address-list \
    address-list=conn_flooder address-list-timeout=1m \
    src-address-list-timeout=1h per-connection-classifier=src-address:32 \
    comment="Detect connection flood"

# ============================================
# Additional Protection Rules
# ============================================

# Protect against DNS amplification
/ip firewall filter
add chain=input protocol=udp dst-port=53 limit=20,5:packet action=accept \
    comment="Allow limited DNS queries"

add chain=input protocol=udp dst-port=53 action=drop \
    comment="Drop excessive DNS queries"

# Protect against NTP amplification
add chain=input protocol=udp dst-port=123 limit=10,5:packet action=accept \
    comment="Allow limited NTP queries"

add chain=input protocol=udp dst-port=123 action=drop \
    comment="Drop excessive NTP queries"

# Protect SSH access
add chain=input protocol=tcp dst-port=22 src-address-list=!$ddosWhitelist \
    connection-state=new action=add-src-to-address-list \
    address-list=ssh_attempt address-list-timeout=1h \
    comment="Track SSH attempts"

add chain=input protocol=tcp dst-port=22 src-address-list=ssh_attempt \
    connection-state=new src-address-list-timeout=1h \
    limit=3,1h:packet action=accept comment="Limit SSH connections"

add chain=input protocol=tcp dst-port=22 src-address-list=ssh_attempt \
    action=drop comment="Drop excessive SSH attempts"

# ============================================
# Logging Rules (Optional)
# ============================================

# Log dropped DDoS traffic (disable if too verbose)
# /ip firewall filter
# add chain=input src-address-list=$ddosBlockList action=log \
#     log-prefix="DDoS-Drop" comment="Log DDoS drops"

# ============================================
# Cleanup Old Rules (Optional)
# ============================================
# This section can be used to remove conflicting rules
# Uncomment with caution

# /ip firewall filter
# :foreach i in=[find comment~"DDoS-Protection-Old"] do={
#     remove $i
# }

:log info "$logPrefix: Configuration complete!"
:log info "$logPrefix: DDoS protection rules installed successfully"
:log info "$logPrefix: Address lists created: $ddosBlockList, $ddosWhitelist"
:log info "$logPrefix: Monitor application can now manage the blocklist"

# ============================================
# Verification Commands
# ============================================
# Run these commands to verify the configuration:
#
# /ip firewall filter print where comment~"DDoS"
# /ip firewall raw print
# /ip firewall address-list print where list=ddos_blocklist
# /ip firewall connection tracking print
