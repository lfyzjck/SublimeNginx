import sublime
import subprocess
import os
import sublime_plugin

settings = sublime.load_settings('Nginx.sublime-settings')


def praseNginxPath():
    path, processName = os.path.split(settings.get('nginx_path'))
    return path

nginx = {
    'status': 'shutted',
    'path': praseNginxPath(),
    'processName': 'nginx.exe' if sublime.platform() == 'windows' else 'nginx'
}


class ShellCommand():

    def execute(self, cmd, path):
        shell = sublime.platform() == "windows"
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, cwd=path, shell=shell)
        stdout, stderr = proc.communicate()
        return stdout

    def call(self, cmd, path):
        #don't read the output
        subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, cwd=path, shell=True)
        return None

    def shell_out(self, cmd):
        return os.popen(cmd)

    def show_errors(self, err, flag = 'status_message'):
        if flag == 'status_message':
            sublime.status_message(err)
        else:
            print err


class NginxCommand(ShellCommand):

    def __new__(cls, *args, **kwargs):
        ''' A pythonic singleton '''
        if '_inst' not in vars(cls):
            cls._inst = super().__new__(cls, *args, **kwargs)
        return cls._inst

    def isAlive(self):
        args = 'tasklist /FO csv /FI "IMAGENAME eq %s"' % nginx.get('processName')
        for line in self.shell_out(args):
            result = line.split(',')
            if result[0] == '"%s"' % nginx.get('processName'):
                return True
        return False

    def updateStatus(self):
        nginx['status'] = 'running' if self.isAlive() else 'shutted'

    def start(self):
        path = nginx.get('path')
        cmd = [os.path.join(path, nginx.get('processName'))]
        return self.call(cmd, path)

    def reload(self):
        path = nginx.get('path')
        cmd = [os.path.join(path, nginx.get('processName')), '-s', 'reload']
        return self.execute(cmd, path)

    def stop(self):
        path = nginx.get('path')
        cmd = [os.path.join(path, nginx.get('processName')), '-s', 'quit']
        return self.execute(cmd, path)


class NginxStartCommand(sublime_plugin.ApplicationCommand, NginxCommand):

    def run(self):
        stdout = self.start()
        if stdout: self.show_errors(stdout)

    def is_enabled(self):
        self.updateStatus()
        return nginx.get('status') == 'shutted'


class NginxStopCommand(sublime_plugin.ApplicationCommand, NginxCommand):

    def run(self):
        stdout = self.stop()
        if stdout: self.show_errors(stdout)

    def is_enabled(self):
        return nginx.get('status') == 'running'


class NginxReloadCommand(sublime_plugin.ApplicationCommand):

    def run(self):
        stdout = self.reload()
        if stdout: self.show_errors(stdout)

    def is_enabled(self):
        return nginx.get('status') == 'running'


class NginxEditConfCommand(sublime_plugin.WindowCommand):
    confPath = os.path.join(nginx.get('path'), 'conf')
    panelItems = []
    def run(self):
        self.panelItems = []
        for i in self.walk_dir(self.confPath):
            self.panelItems.append(i) 
        self.window.show_quick_panel(self.panelItems, self.open_file)

    def is_enabled(self):
        return os.path.exists(self.confPath)

    def open_file(self, f):
        if f == -1: return
        self.window.open_file(self.panelItems[f])

    def walk_dir(self, dirname):
        for root,dirs,files in os.walk(dirname):
            for f in files:
                if f.endswith(".conf"):
                    yield os.path.join(root, f) 
