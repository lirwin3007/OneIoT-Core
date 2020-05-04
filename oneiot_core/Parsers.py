import os.path as path

class DHCPDParser():

    def __init__(self, configPath):
        self.path = configPath
        if path.exists(configPath):
            self.raw = open(configPath).read()
        else:
            self.raw = ""
        self.modified = self.raw
        self.parse()


    def parse(self):
        lines = self.raw.split("\n")
        last_interface = None
        interfaces = {}
        for line in lines:
            if len(line) == 0:
                continue
            if line[0] == "#":
                continue
            splitLine = line.split(" ")
            if splitLine[0] == "interface":
                last_interface = splitLine[1]
                if splitLine[1] not in interfaces:
                    interfaces[splitLine[1]] = []
            elif splitLine[0][0:1] != "\t":
                last_interface = None
            elif last_interface is not None:
                if splitLine[0][0:1] == "\t":
                    splitLine[0] = splitLine[0][1:]
                    interfaces[last_interface].append(splitLine)
        self.interfaces = interfaces

    def modifyInterface(self, interface, options):
        result = ""
        in_interface = False
        for line in self.modified.split("\n"):
            if len(line) == 0:
                continue
            if line[0] == "#":
                continue
            splitLine = line.split(" ")
            if splitLine[0] == "interface":
                if splitLine[1] == interface:
                    in_interface = True
            elif splitLine[0][0:1] != "\t":
                in_interface = False
            if not in_interface:
                result += line + "\n"
        result += f"interface {interface}\n"
        for option in options:
            result += f"\t{option[0]}"
            for suboption in option[1:]:
                result += f" {suboption}"
            result += "\n"
        self.modified = result

    def save(self):
        f = open(self.path, "w")
        f.write(self.modified)
        f.close()

class HostAPDParser():

    def __init__(self, configPath, masterConfigPath):
        self.configPath = configPath
        if path.exists(configPath):
            self.raw = open(configPath).read()
        else:
            self.raw = ""
        self.masterConfigPath = masterConfigPath
        if path.exists(masterConfigPath):
            self.master_raw = open(masterConfigPath).read()
        else:
            self.master_raw = ""
        self.modified = self.raw
        self.master_modified = self.master_raw
        self.parse()
        self.parse_master()

    def parse(self):
        lines = self.raw.split("\n")
        self.options = {x.split("=")[0]: x.split("=")[1] for x in lines if len(x) > 0 and x[0] != "#"}

    def parse_master(self):
        lines = self.master_raw.split("\n")
        self.options_master = {x.split("=")[0]: x.split("=")[1] for x in lines if len(x) > 0 and x[0] != "#"}

    def set_options(self, options):
        result = ""
        for option in options:
            result += f"{option}={options[option]}\n"
        self.modified = result

    def set_master_options(self, options):
        result = ""
        for option in options:
            result += f"{option}={options[option]}\n"
        self.master_modified = result

    def save(self):
        f = open(self.configPath, "w")
        f.write(self.modified)
        f.close()

    def save_master(self):
        f = open(self.masterConfigPath, "w")
        f.write(self.master_modified)
        f.close()

class DNSMasqParser():

    def __init__(self, configPath):
        self.path = configPath
        if path.exists(configPath):
            self.raw = open(configPath).read()
        else:
            self.raw = ""
        self.modified = self.raw
        self.parse()

    def set_options(self, dict, list):
        result = ""
        for option in dict:
            result += f"{option}={dict[option]}\n"
        for option in list:
            result += f"{option}\n"
        self.modified = result

    def save(self):
        f = open(self.path, "w")
        f.write(self.modified)
        f.close()

    def parse(self):
        lines = self.raw.split("\n")
        self.option_dict = {}
        self.option_list = []
        for line in lines:
            split = line.split("=")
            if len(split) > 1:
                self.option_dict[split[0]]=split[1]
            else:
                self.option_list.append(split[0])

class EnvParser():

    def __init__(self, configPath):
        self.path = configPath
        if path.exists(configPath):
            self.raw = open(configPath).read()
        else:
            self.raw = ""
        self.parse()

    def parse(self):
        lines = self.raw.split("\n")
        self.vars = {x.split("=")[0]: x.split("=")[1] for x in lines if len(x) > 0 and x[0] != "#"}

    def save(self):
        f = open(self.path, "w")
        for var in self.vars:
            f.write(f"{var}={self.vars[var]}\n")
        f.close()
