This has been tested on Ubuntu 14.04 with the following software already installed

* Python 2.7
* Ansible 2.1 or greater

To install the software on localhost

    ./deploy.sh

To view the Prometheus web UI go to

    http://localhost:9090

To see the metrics exporters configured within Prometheus

    http://localhost:9090/targets

To view the Grafana web UI (user: admin, password: password) go to

    http://localhost:3000

To see the Alertmanager web UI go to

    http://localhost:9093

To make repeated HTTP calls that will trigger the `HighRequestRate` alert:

    while true; do
        curl -X POST http://localhost:8002
        sleep 1
    done

To see a log of the alerts raised by the above (note may take a minute or two to appear):

    less -n +F /tmp/input.log

To view the RabbitMQ management web UI (user: admin, password: password) go to

    http://localhost:15672
    
To call the **Hello World** API:

    curl -H "Content-Type: application/json" -X POST -d '{"foo":"abc","bar":"xyz"}' http://localhost:8001

To call the **Post RabbitMQ Message** API:

    curl -X POST http://localhost:8002

To call the **General Process Metrics** API:

    curl -X POST http://localhost:8003/metrics

To run UWSGI-top for viewing UWSGI statistics

    pip install uwsgitop
    # Hello world app
    uwsgitop http://localhost:3101
    # Post RabbitMQ message app
    uwsgitop http://localhost:3102
    # General process metrics app
    uwsgitop http://localhost:3103
