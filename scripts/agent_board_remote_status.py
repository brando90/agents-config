"""Read bounded, allowlisted job receipts; executed by the board over SSH, without models."""
import datetime
import json
import pathlib
import subprocess
import time


def read_record(path):
    try:
        with path.open('rb') as stream:
            raw = stream.read(262145)
        if len(raw) > 262144:
            return {}
        value = json.loads(raw)
        return value if isinstance(value, dict) else {}
    except (OSError, ValueError):
        return {}


def process_alive(identity):
    if not isinstance(identity, dict) or not identity:
        return None
    try:
        raw_pid = identity.get('pid')
        if type(raw_pid) is not int and not (isinstance(raw_pid, str) and raw_pid.isdecimal()):
            return None
        pid = int(raw_pid)
        if pid <= 0:
            return None
        boot = pathlib.Path('/proc/sys/kernel/random/boot_id').read_text().strip()
        # comm may contain spaces or parentheses: split after its last closing parenthesis.
        fields = pathlib.Path(f'/proc/{pid}/stat').read_text().rsplit(')', 1)[1].split()
        return (boot == identity['boot_id'] and fields[19] == str(identity['start_ticks'])
                and fields[0] != 'Z')
    except FileNotFoundError:
        return False
    except (OSError, ValueError, TypeError, KeyError, IndexError):
        return None


def receipt_age(record, now):
    stamp = record.get('at') or record.get('timestamp') or record.get('acknowledged_at')
    try:
        value = datetime.datetime.fromisoformat(stamp.replace('Z', '+00:00'))
        if value.tzinfo is None:
            return None
        age = now - value.timestamp()
        return age if age >= -5 else None
    except (ValueError, TypeError, AttributeError):
        return None


def job_status(name, cwd, now):
    # Existing workers keep their receipts beside repo/. No recursive filesystem scan.
    base = pathlib.Path(cwd).parent
    ack = read_record(base / 'acknowledgement.json')
    if ack.get('session') != name or ack.get('cwd') != cwd:
        return None
    progress = read_record(base / 'progress.json')
    driver = read_record(base / 'driver_identity.json')
    watchdog = read_record(base / 'watchdog.json')
    identity = {'pid': ack.get('coordinator_pid', ack.get('pid')),
                'start_ticks': ack.get('coordinator_start_ticks', ack.get('process_start_ticks')),
                'boot_id': ack.get('boot_id')}
    run_id = ack.get('run_id')
    bound = {key: bool(isinstance(run_id, str) and run_id and record.get('run_id') == run_id)
             for key, record in [('progress', progress), ('driver', driver), ('watchdog', watchdog)]}
    result = {'run_binding': bound, 'observed_at': now, 'coordinator_alive': process_alive(identity),
              'driver_alive': process_alive(driver.get('process')) if bound['driver'] else None,
              'progress_age': receipt_age(progress, now),
              'watchdog_age': receipt_age(watchdog, now),
              'watchdog_status': str(watchdog.get('status', 'unknown'))[:80] if bound['watchdog'] else 'unbound receipt'}
    # Never forward raw receipts, environment, command lines or credentials.
    for key in ('generated', 'scored', 'planned'):
        value = progress.get(key)
        if type(value) is int and value >= 0:
            result[key] = value
    result['phase'] = str((progress.get('phase') if bound['progress'] else ack.get('phase')) or 'unknown')[:100]
    return result


def main():
    panes = subprocess.run(['tmux', 'list-panes', '-a', '-F',
                            '#{session_name}\t#{pane_current_path}'],
                           capture_output=True, text=True, timeout=3)
    if panes.returncode:
        print('{}')
        return
    output = {}
    for line in panes.stdout.splitlines()[:200]:
        fields = line.split('\t', 1)
        if len(fields) == 2:
            status = job_status(*fields, time.time())
            if status is not None:
                output[fields[0]] = status
    print(json.dumps(output))


if __name__ == '__main__':
    main()
