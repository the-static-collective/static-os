"""Frozen desktop entry: no pip, checkout, or host Python at launch time."""
import fcntl
import os
from pathlib import Path
import subprocess
import sys
import threading
import time
import webbrowser


def notify(message):
    print(message, file=sys.stderr)
    try:
        subprocess.run(['zenity', '--error', '--title=Static Workbench', '--text=' + message], check=False)
    except OSError:
        pass


def main():
    if '--self-test' in sys.argv:
        from static_workbench.app import create_app
        from static_workbench.config import load_config
        app = create_app(load_config())
        assert any(getattr(route, 'path', None) == '/' for route in app.routes)
        import static_workbench
        assert (Path(static_workbench.__file__).parent / 'web/index.html').is_file()
        print('Bundled Workbench imports and app construction: OK')
        return
    if os.getuid() == 0:
        notify('Open Static Workbench from your normal desktop account.')
        return
    from static_workbench.config import load_config
    import uvicorn
    from static_workbench.app import create_app
    config = load_config()
    host = '[' + config.bind_host + ']' if ':' in config.bind_host else config.bind_host
    url = f'http://{host}:{config.port}/'
    state = Path.home() / '.local/state/static-workbench-desktop'
    state.mkdir(parents=True, exist_ok=True, mode=0o700)
    with (state / 'launcher.lock').open('a') as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            webbrowser.open(url)
            return
        with (state / 'server.log').open('a', buffering=1) as log:
            os.dup2(log.fileno(), 1)
            os.dup2(log.fileno(), 2)
            server = uvicorn.Server(uvicorn.Config(create_app(config), host=config.bind_host,
                                    port=config.port, access_log=False))
            def open_when_ready():
                for _ in range(300):
                    if server.started:
                        webbrowser.open(url)
                        return
                    time.sleep(0.1)
            threading.Thread(target=open_when_ready, daemon=True).start()
            try:
                server.run()
            except (Exception, SystemExit):
                notify('Workbench could not start. Another copy may be using its port. Details: ' + str(state / 'server.log'))
                raise


if __name__ == '__main__':
    try:
        main()
    except Exception as exc:
        notify('Workbench needs attention: ' + str(exc))
        raise
