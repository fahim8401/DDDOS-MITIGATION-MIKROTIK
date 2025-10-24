# MikroTik DDoS Mitigation Scripts
# RouterOS v7 compatible
# Import this file to each MikroTik router to enable DDoS protection
# DO NOT import if you have custom firewall rules - review first!

# WARNING: These scripts modify firewall rules. Test in lab environment first.
# These rules throttle traffic but do NOT block ports to avoid breaking services.

# DDoS Tighten Script
# Increases connection limits and adds rate limiting during attacks
/system script add name=ddos-tighten source="\
# DDoS Tighten - Increase security limits\
/ip firewall filter {\
  set [find comment~\"ddos-conn-limit\"] limit=50,10:packet burst=100,20:packet action=drop;\
  set [find comment~\"ddos-new-conn\"] limit=30,5:packet burst=50,10:packet action=drop;\
  set [find comment~\"ddos-syn-limit\"] limit=100,20:packet burst=200,50:packet action=drop;\
}\
/ip firewall connection tracking set maximum=10000\
"

# DDoS Restore Script
# Restores normal connection limits after attack subsides
/system script add name=ddos-restore source="\
# DDoS Restore - Return to normal limits\
/ip firewall filter {\
  set [find comment~\"ddos-conn-limit\"] limit=200,50:packet burst=500,100:packet action=drop;\
  set [find comment~\"ddos-new-conn\"] limit=100,20:packet burst=200,50:packet action=drop;\
  set [find comment~\"ddos-syn-limit\"] limit=500,100:packet burst=1000,200:packet action=drop;\
}\
/ip firewall connection tracking set maximum=50000\
"

# Address List Management Scripts
/system script add name=add-attack source="\
# Add attacking IP to address list\
:if ([:len \$1] > 0) do={ /ip firewall address-list add list=ddos_blocklist address=\$1 timeout=1h comment=\"Auto-blocked\" }\
"

/system script add name=remove-attack source="\
# Remove IP from address list\
:if ([:len \$1] > 0) do={ /ip firewall address-list remove [find list=ddos_blocklist address=\$1] }\
"

# Firewall Rules
# These rules should be placed at the top of your filter chain
# Adjust interface names as needed

# Connection limit per source IP
/ip firewall filter add chain=input protocol=tcp connection-limit=200,50:packet burst=500,100:packet action=drop comment="ddos-conn-limit" place-before=0

# New connection rate limit
/ip firewall filter add chain=input protocol=tcp tcp-flags=syn connection-state=new limit=100,20:packet burst=200,50:packet action=drop comment="ddos-new-conn" place-before=0

# SYN flood protection
/ip firewall filter add chain=input protocol=tcp tcp-flags=syn limit=500,100:packet burst=1000,200:packet action=drop comment="ddos-syn-limit" place-before=0

# UDP flood protection (adjust as needed)
/ip firewall filter add chain=input protocol=udp limit=1000,200:packet burst=2000,500:packet action=drop comment="ddos-udp-limit" place-before=0

# ICMP flood protection
/ip firewall filter add chain=input protocol=icmp limit=50,10:packet burst=100,20:packet action=drop comment="ddos-icmp-limit" place-before=0

# Block address list (place this rule high in your chain)
/ip firewall filter add chain=input src-address-list=ddos_blocklist action=drop comment="ddos-blocklist" place-before=0

# Address list for blocked IPs
/ip firewall address-list add list=ddos_blocklist comment="DDoS blocked IPs"

# Connection tracking settings
/ip firewall connection tracking set maximum=50000 tcp-timeout=2h udp-timeout=30s

# Note: These rules throttle but don't block ports
# Monitor your services after applying
# Adjust limits based on your normal traffic patterns