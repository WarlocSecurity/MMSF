import os
import shutil
from signal import SIGINT
import tempfile
import subprocess
from colorama import Fore
from subprocess import DEVNULL, PIPE
from Classes.constants import Constants
from Classes.utils import execute_frida_command, find_command

class Frida:
    _config: dict

    @property
    def config(self):
        return self._config

    @config.setter
    def config(self, data):
        self._config = data

    def __repr__(self) -> str:
        pass

    def __hash__(self) -> int:
        return hash(self.id)

    def __eq__(self, __o: object) -> bool:
        """Compare two class instances."""
        if __o.id == self.id:
            return True
        return False

    def __init__(self, low_power_mode=False) -> None:
        self.__init_frida()
        self.low_power_mode = low_power_mode
        self._config = {
            "mode": "-U",
            "app": "",
            "host": "127.0.0.1",
            "pause": "",
            "method": "-f"
        }
        self.temp_dir = tempfile.mkdtemp()
        self.temp_file = tempfile.mkstemp(dir=self.temp_dir, suffix=".js")[1]
        self.files = {'ssl-android': os.path.join(self.temp_dir,'frida-ssl-android.log'), 
                      'root-android': os.path.join(self.temp_dir,'frida-root-android.log'), 
                      'biometrics-ios': os.path.join(self.temp_dir,'frida-biometrics-ios.log'),
                      'jailbreak-ios': os.path.join(self.temp_dir,'frida-jailbreak-ios.log')}
        
        for file in self.files.keys():
            if (os.path.exists(self.files[file])):
                os.remove(self.files[file])
    
    def __del__(self):
        shutil.rmtree(self.temp_dir)

    def __init_frida(self):
        common_paths = ["/tmp/frida-server", "/data/local/tmp/frida-server"]
        for fpath in common_paths:
            p = subprocess.run(f'{Constants.ADB.value} shell ls {fpath}'.split(), stderr=PIPE, stdout=PIPE)
            if any("No such file or directory" in s for s in [p.stderr.decode(), p.stdout.decode()]):
                continue
            cmd = f'{Constants.ADB.value} shell su -c "{fpath} &"'
            p = subprocess.Popen(cmd.split(), stdin=PIPE, stderr=PIPE, stdout=PIPE)

        subprocess.run([Constants.ADB.value, 'forward', 'tcp:27042', 'tcp:27042'], stderr=DEVNULL, stdout=DEVNULL)

        p = subprocess.run(['frida-ps', '-U'], stdout=PIPE, stderr=PIPE)
        if "Failed to enumerate processes: unable to find process with name 'system_server'" in p.stdout.decode():
            print(Fore.RED + '[-] frida is missing. Check your installation or install via mmsfupdate frida_server... Exitting... ')
            quit()

        print(Fore.BLUE + '[*] Frida is running' + Fore.RESET)

    def copy_file(self, type, api_v=''):
        if type == "ssl":
            file = 'Frida_Scripts/bypass_ssl_pinning_various_methods.js'
        elif type == "root":
            file = 'Frida_Scripts/antiroot_bypass.js'
        elif type == "ios_biometrics":
            file = 'Frida_Scripts/Fingerprint_bypasses/fingerprint-bypass-ios.js'
        elif type == "android_biometrics":
            file = f'Frida_Scripts/Fingerprint_bypasses/fingerprint-android-{api_v}.js'
        elif type == "android_biometrics_crypto":
            file = 'Frida_Scripts/Fingerprint_bypasses/fingerprint-bypass-via-exception-handling.js'
        elif type == "ios_jailbreak_bypass":
            file = 'Frida_Scripts/ios-jailbreak-detection-bypass.js'
        else:
            file = tempfile.mkstemp(dir=self.temp_dir, suffix=".js")
        
        with open(self.temp_file,'r') as secondfile:
            for line in secondfile:
                if (type == "root" and "[+] Antiroot bypass [+]" in line) or (type == "ssl" and "[#] Android Bypass for various Certificate Pinning methods [#]" in line) or (type == "ios_jailbreak_bypass" and "jailbreakPaths" in line):
                    return
        
        with open(file,'r') as firstfile, open(self.temp_file,'a') as secondfile:
            # read content from first file
            for line in firstfile:
                # write content to second file
                secondfile.write(line)

    def bypass_ssl(self):
        def exec_running():
            self.copy_file("ssl")
            print(Fore.GREEN + '[+] The command was executed successfully!' + Fore.RESET)
            
        def exec_new():
            self.copy_file("ssl")
            outfile = self.files['ssl-android']
            execute_frida_command(self.config, self.temp_file, outfile, 'frida')

        found = find_command('frida', self.config["app"])
        if not found:
            exec_new()
        else:
            exec_running()

    def bypass_root(self):
        def exec_running():
            self.copy_file("root")
            print(Fore.GREEN + '[+] The command was executed successfully!' + Fore.RESET)
            
        def exec_new():
            self.copy_file("root")
            outfile = self.files['root-android']
            execute_frida_command(self.config, self.temp_file, outfile, 'frida')

        found = find_command('frida', self.config["app"])
        if not found:
            exec_new()
        else:
            exec_running()
            
    def bypass_ios_biometrics(self):
        def exec_running():
            self.copy_file("ios_biometrics")
            print(Fore.GREEN + '[+] The command was executed successfully!' + Fore.RESET)
            
        def exec_new():
            self.copy_file("ios_biometrics")
            cmd = f'frida {self._config["mode"]} {self.config["method"]} {self._config["app"]} -l {self.temp_file} {self._config["pause"]}'
            outfile = self.files['biometrics-ios']
            execute_frida_command(cmd, outfile, 'frida')

        found = find_command('frida', self.config["app"])
        if not found:
            exec_new()
        else:
            exec_running()
            
    def bypass_android_biometrics(self):
        def exec_running():
            self.copy_file("android_biometrics", api_version)
            print(Fore.GREEN + '[+] The command was executed successfully!' + Fore.RESET)
            
        def exec_new():
            self.copy_file("android_biometrics", api_version)
            cmd = f'frida {self._config["mode"]} {self.config["method"]} {self._config["app"]} -l {self.temp_file} {self._config["pause"]}'
            outfile = self.files['biometrics-ios']
            execute_frida_command(cmd, outfile, 'frida')

        api_version = subprocess.run(f'{Constants.ADB.value} shell getprop ro.build.version.release'.split(), stdout=PIPE, stderr=DEVNULL).stdout.decode().strip().split('.')[0]
        print(Fore.BLUE + f'[*] Detected Android API v{api_version}' + Fore.RESET)
        found = find_command('frida', self.config["app"])
        if not found:
            exec_new()
        else:
            exec_running()
            
    def bypass_android_biometrics_crypto_object(self):
        def exec_running():
            self.copy_file("android_biometrics_crypto")
            print(Fore.GREEN + '[+] The command was executed successfully!' + Fore.RESET)
            
        def exec_new():
            self.copy_file("android_biometrics_crypto")
            cmd = f'frida {self._config["mode"]} {self.config["method"]} {self._config["app"]} -l {self.temp_file} {self._config["pause"]}'
            outfile = self.files['biometrics-ios']
            execute_frida_command(cmd, outfile, 'frida')

        found = find_command('frida', self.config["app"])
        if not found:
            exec_new()
        else:
            exec_running()
            
    def bypass_ios_jailbreak(self):
        def exec_running():
            self.copy_file("ios_jailbreak_bypass")
            print(Fore.GREEN + '[+] The command was executed successfully!' + Fore.RESET)
            
        def exec_new():
            self.copy_file("ios_jailbreak_bypass")
            cmd = f'frida {self._config["mode"]} {self.config["method"]} {self._config["app"]} -l {self.temp_file} {self._config["pause"]}'
            outfile = self.files['jailbreak-ios']
            execute_frida_command(cmd, outfile, 'frida')

        found = find_command('frida', self.config["app"])
        if not found:
            exec_new()
        else:
            exec_running()