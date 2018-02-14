import json
import os
import pprint


def application(env, start_response):
    start_response('200 OK', [('Content-Type', 'text/html')])
    response = list()
    response.append('Raw data:')
    for key in sorted(env.keys()):
        response.append('  {}: {}'.format(key, env[key]))
    if 'wsgi.input' in env:
        input_data = env['wsgi.input'].readline()
        with open('/tmp/input.log', 'a') as the_file:
            the_file.write(input_data)
            the_file.write('\n')
        response.append('')
        try:
            input_data_dict = json.loads(input_data)
            response.append('Input data:')
            response.append(pprint.pformat(input_data_dict))
        except ValueError:
            response.append('Input data: {}'.format(input_data))
    return os.linesep.join(response)
