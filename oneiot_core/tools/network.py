import os.path as path

import netifaces
from pystemd.systemd1 import Unit

import oneiot_core.env as env
import oneiot_core.Parsers as Parsers

def get_status():
    # Get setup status
    interface_selected_status = get_interface_selected_status()
    static_ip_set_up_status = get_static_ip_set_up_status()
    hostapd_setup_status = get_hostapd_setup_status()
    dnsmasq_setup_status = get_dnsmasq_setup_status()
    # Get status
    static_ip_respected_status = get_static_ip_respected_status()
    hostapd_running_status = get_hostapd_running_status()
    dnsmasq_running_status = get_dnsmasq_running_status()
    return {"setup": [
            {"name": "Network Interface Selected", "status": interface_selected_status},
            {"name": "Static IP Set Up", "status": static_ip_set_up_status},
            {"name": "Hostapd Set Up", "status": hostapd_setup_status},
            {"name": "DNSMasq Set Up", "status": dnsmasq_setup_status},
        ],
        "status": [
            {"name": "Static IP Respected", "status": static_ip_respected_status},
            {"name": "HostAPD Running", "status": hostapd_running_status},
            {"name": "DNSMasq Running", "status": dnsmasq_running_status},
        ]
    }

def get_interface_selected_status():
    interfaces = netifaces.interfaces()
    return env.var("ONEIOT_C_NETWORK_INTERFACE") in interfaces

def get_static_ip_set_up_status():
    dhcpcd = Parsers.DHCPDParser("/etc/dhcpcd.conf")
    interface = env.var("ONEIOT_C_NETWORK_INTERFACE")
    static_ip = env.var("ONEIOT_C_STATIC_IP")
    if interface in dhcpcd.interfaces:
        for option in dhcpcd.interfaces[interface]:
            if option[0] == "static":
                return option[1] == f"ip_address={static_ip}/24"
    else:
        return False

def get_hostapd_setup_status():
    interface = env.var("ONEIOT_C_NETWORK_INTERFACE")
    ssid = env.var("ONEIOT_C_NETWORK_SSID")
    hostapd = Parsers.HostAPDParser("/etc/hostapd/hostapd.conf", "/etc/default/hostapd")

    options = hostapd.options
    result = options['interface'] == interface
    result = result and options['driver'] == 'nl80211'
    result = result and options['ssid'] == ssid
    result = result and options['hw_mode'] == 'g'
    result = result and options['channel'] == '6'
    result = result and options['ieee80211n'] == '1'
    result = result and options['wmm_enabled'] == '1'
    result = result and options['ht_capab'] == '[HT40][SHORT-GI-20][DSSS_CCK-40]'
    result = result and options['macaddr_acl'] == '0'
    result = result and options['auth_algs'] == '1'
    result = result and options['ignore_broadcast_ssid'] == '0'
    result = result and options['wpa'] == '2'
    result = result and options['wpa_key_mgmt'] == 'WPA-PSK'
    result = result and options['wpa_passphrase'] == env.network_password()
    result = result and len(env.network_password()) >= 8
    result = result and len(env.network_password()) <= 63
    result = result and options['rsn_pairwise'] == 'CCMP'

    options_master = hostapd.options_master
    result = result and options_master['DAEMON_CONF'] == '"/etc/hostapd/hostapd.conf"'

    return result

def get_dnsmasq_setup_status():
    interface = env.var("ONEIOT_C_NETWORK_INTERFACE")
    static_ip = env.var("ONEIOT_C_STATIC_IP")
    static_ip_split = static_ip.split(".")

    if not path.exists("/etc/dnsmasq.conf"):
        return False

    dnsmasq = Parsers.DNSMasqParser("/etc/dnsmasq.conf")

    result = dnsmasq.option_dict['interface'] == interface
    result = result and dnsmasq.option_dict['server'] == '8.8.8.8'
    result = result and dnsmasq.option_dict['dhcp-range'] == f'{static_ip_split[0]}.{static_ip_split[1]}.{static_ip_split[2]}.2,{static_ip_split[0]}.{static_ip_split[1]}.{static_ip_split[2]}.254,255.255.255.0,24h'
    result = result and 'bind-interfaces' in dnsmasq.option_list
    result = result and 'domain-needed' in dnsmasq.option_list
    result = result and 'bogus-priv' in dnsmasq.option_list

    return result

def get_static_ip_respected_status():
    interface = env.var("ONEIOT_C_NETWORK_INTERFACE")
    ifconfig = netifaces.ifaddresses(interface)

    if netifaces.AF_INET in ifconfig:
        if len(ifconfig[netifaces.AF_INET]) > 0:
            return ifconfig[netifaces.AF_INET][0]['addr'] == env.var("ONEIOT_C_STATIC_IP")
        else:
            return False
    else:
        return False

def get_hostapd_running_status():
    unit = Unit(b'hostapd.service')
    unit.load()
    return unit.Unit.ActiveState == b'active'

def get_dnsmasq_running_status():
    unit = Unit(b'dnsmasq.service')
    unit.load()
    return unit.Unit.ActiveState == b'active'

def restart_services():
    hostapd = Unit(b'hostapd.service')
    hostapd.load()
    hostapd.Unit.Restart(b'replace')
    dnsmasq = Unit(b'dnsmasq.service')
    dnsmasq.load()
    dnsmasq.Unit.Restart(b'replace')
