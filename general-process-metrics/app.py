import sys
import traceback

from prometheus_client import ProcessCollector, generate_latest
import psutil


_PROCESSES = {
    'echo_uwsgi_parameters': ['echo-uwsgi-parameters'],
    'general_process_metrics': ['general-process-metrics'],
    'post_rabbitmq_message': ['post-rabbitmq-message']}


def application(env, start_response):
    try:
        for namespace, search_terms in _PROCESSES.items():
            found_processes = _find_processes_matching(search_terms)
            # Many flaws in this, assumes single master and optionally multiple child workers
            master_pids = set()
            for process in found_processes.values():
                if process.ppid() in found_processes.keys():
                    master_pids.add(process.ppid())
            master_pids = sorted(master_pids)
            child_pids = sorted({pid for pid in found_processes.keys() if pid not in master_pids})
            for master_pid in master_pids:
                # Annoying we cannot seem to use labels easily (without making ourselves). The
                # process collector is probably too limited for what we would want.
                pid_namespace = '{}_master'.format(namespace)
                try:
                    ProcessCollector(namespace=pid_namespace, pid=lambda: master_pid).collect()
                except Exception as ex:
                    print 'Unable to collect stats for {}, PID {}: {}'.format(pid_namespace, master_pid, ex.message)
            for index, child_pid in enumerate(child_pids):
                pid_namespace = '{}_worker_{}'.format(namespace, index)
                try:
                    ProcessCollector(namespace=pid_namespace, pid=lambda: child_pid).collect()
                except Exception as ex:
                    print 'Unable to collect stats for {}, PID {}: {}'.format(pid_namespace, child_pid, ex.message)
        start_response('200 OK', [('Content-Type', 'text/html')])
        return generate_latest()
    except Exception as ex:
        print ex.message
        traceback.print_tb(sys.exc_info()[2])
        start_response('500 INTERNAL SERVER ERROR', [('Content-Type', 'text/html')])
        return ex.message


def _find_processes_matching(search_terms):
    found_processes = dict()
    for process in psutil.process_iter():
        if _process_matches(process, search_terms):
            found_processes[process.pid] = process

    return found_processes


def _process_matches(process, search_terms):
    for search_term in search_terms:
        try:
            if not _search_term_in_cmd_line(search_term, process.cmdline()):
                return False
        except psutil.AccessDenied:
            return False
    return True


def _search_term_in_cmd_line(search_term, cmd_line):
    for cmd_line_part in cmd_line:
        if search_term in cmd_line_part:
            return True
    return False
