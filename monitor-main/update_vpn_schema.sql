-- Add columns for VPN Breakdown
alter table router_stats
add column vpn_l2tp int default 0,
add column vpn_ovpn int default 0,
add column vpn_pptp int default 0,
add column vpn_sstp int default 0;
