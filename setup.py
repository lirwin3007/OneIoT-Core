from setuptools import setup, find_packages
from setuptools.command.install import install

with open("README.md", "r") as fh:
    long_description = fh.read()

class CustomInstallCommand(install):
    def run(self):
        import os, re, sys, subprocess, getpass
        try:
            import httplib
        except:
            import http.client as httplib
        import datetime
        import configparser

        def print_message(status, message, include_time = False):
            print('[' + status + ']\t' + message + ('\t' + str(datetime.datetime.now().strftime('%M:%S.%f')) if include_time else ''))

        def check_internet_connection():
            print_message('INFO', 'Checking for an active internet connection...')
            while True:
                conn = httplib.HTTPConnection("www.google.com", timeout=5)
                try:
                    conn.request("HEAD", "/")
                    conn.close()
                    print_message('INFO', 'Internet connection found!')
                    return True
                except:
                    conn.close()
                    print_message('WARN', 'No internet connection found. Please connect to the internet and press [ENTER] to continue.')
                    input("")

        def is_valid_network_name(name):
            return re.match('^\w+$', name)

        if not __name__ == '__main__':
            print_message('FATAL', 'Not executing as top level code')
            exit()

        os.system("clear")
        print("OneIoT Core setup")
        print()
        print("Please ensure that you are connected to the internet")
        print("Press [ENTER] to continue")
        input()

        # Check internet connection
        check_internet_connection()

        #Hotspot setup
        print_message("INFO", "Setting up wireless hotspot\n")
        network_name = input("Enter a name for the wireless network used to connect smart device (default: OneIoT): ")
        if network_name == "":
            network_name = "OneIoT"
        while not is_valid_network_name(network_name):
            network_name = input("Invalid network name, please enter only alphanumeric characters, or press enter to use the default value:")
            if network_name == "":
                network_name = "OneIoT"

        network_password = getpass.getpass("Enter a secure password: ")
        while network_password == "":
            network_password = getpass.getpass("Enter a secure password: ")

        confirm_password = getpass.getpass("Confirm password: ")
        while confirm_password != network_password:
            confirm_password = getpass.getpass("Confirm password: ")

        #Configure static ip
        os.system("printf 'interface wlan0\n\tstatic ip_address=192.168.4.1/24\n\tnohook wpa_supplicant' | sudo tee -a /etc/dhcpcd.conf")
        os.system("sudo systemctl restart dhcpcd")

        #Configure hostapd
        hostapd_config = "interface=wlan0\ndriver=nl80211\nssid=" + network_name + "\nhw_mode=g\nchannel=6\nieee80211n=1\nwmm_enabled=1\nht_capab=[HT40][SHORT-GI-20][DSSS_CCK-40]\nmacaddr_acl=0\nauth_algs=1\nignore_broadcast_ssid=0\nwpa=2\nwpa_key_mgmt=WPA-PSK\nwpa_passphrase=" + network_password + "\nrsn_pairwise=CCMP"
        os.system("printf '" + hostapd_config + "' | sudo tee /etc/hostapd/hostapd.conf")
        os.system("printf 'DAEMON_CONF=\"/etc/hostapd/hostapd.conf\"' | sudo tee -a /etc/default/hostapd")

        #Configure dnsmasq
        dnsmasq_config = "interface=wlan0\nbind-interfaces\nserver=8.8.8.8\ndomain-needed\nbogus-priv\ndhcp-range=192.168.4.2,192.168.4.20,255.255.255.0,24h"
        os.system("sudo mv /etc/dnsmasq.conf /etc/dnsmasq.conf.orig")
        os.system("sudo touch /etc/dnsmasq.conf")
        os.system("printf '" + dnsmasq_config + "' | sudo tee /etc/dnsmasq.conf")

        #IPV4 forwarding
        os.system("printf 'net.ipv4.ip_forward=1' | sudo tee -a /etc/sysctl.conf")
        os.system("sudo sh -c 'echo 1 > /proc/sys/net/ipv4/ip_forward'")

        #Restart services
        os.system("sudo systemctl unmask hostapd")
        os.system("sudo systemctl enable hostapd")
        os.system("sudo systemctl start hostapd")
        os.system("sudo service dnsmasq start")
        print_message("INFO", "Completed setting up wireless hotspot")

        config = configparser.ConfigParser()
        config['wireless-info'] = {'ssid':network_name, 'psk':network_password}

        oneIot_path = os.path.expanduser("~/.oneIot")

        if not os.path.exists(oneIot_path):
            os.makedirs(oneIot_path)

        with open(oneIot_path + "/config.ini", 'w') as configfile:
            config.write(configfile)

        os.system("clear")
        print("Device setup complete! please reboot now")

        install.run(self)

setup(
    name="oneiot-core",
    version="0.0.1",
    author="Louis Irwin",
    author_email="coding@louisirwin.co.uk",
    description="OneIoT Core",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/lirwin3007/OneIoT-Core",
    packages=find_packages(),
    python_requires='>=3.6',
    cmdclass={
        'install': CustomInstallCommand
    }
)
