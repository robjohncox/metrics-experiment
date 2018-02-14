# UWSGI, Prometheus, Grafana and Alertmanager

This document summarises a research project to evaluate four technologies

* **UWSGI**: a web server, specifically the ease of hosting multiple lightweight applications that
  use the HTTP protocol.
* **Prometheus**: a system for collecting, storing and exposing time series metrics, along with a
  custom query language.
* **Grafana**: a web based dashboard interface that integrates closely with Prometheus and enables
  creation of dashboards & re-use of ones already created and available online.
* **Alertmanager**: a general alerts handling system that integrates closely with Prometheus and
  provides a rule based system and web UI for managing alerts.

This does not give a comprehensive overview of these technologies, and I don't claim this is the
best writing you ever saw. Also, UWSGI may seem like a strange thing to group with the other pieces
of software, however (a) I wanted to take a deeper dive at the same time and (b) it was useful to
be able to write lightweight web apps for parts of the example code, so it is here.

## Running the example code

To really get a feel for these systems, you should fire up the example code that was built as
part of this research and have a play around:

* Fire up an Ubuntu box (ideally a one-off VM, as this will install a lot of software)
* Clone https://github.com/robjohncox/metrics-experiment
* Run `./deploy.sh`
* Go to `README.md` for instructions on how to use and test the various applications

Please note that this example is running old versions of the software, this was what was installed
by the playbooks sourced from Ansible Galaxy. These proved perfectly fine for the purpose of this
evaluation.

## Appraisal of individual technologies

### UWSGI

https://uwsgi-docs.readthedocs.io/en/latest/

UWSGI is an application server that can host web applications written in a number of languages,
including Python. We wanted to see how easy it is to write small applications in pure Python,
without using a web framework, that respond to HTTP requests, and host these on a server.

It turns out to be trivial:

* You write a function that takes in a dictionary of HTTP metadata and a function used to push
  back a response. You can get the request URI, headers and any other request data easily, do
  your thing, and then use the response function to provide a response status code and response
  headers (including content type). Finally, you return the response content, HTML, JSON, whatever.
* A small UWSGI configuration file wires this function to the UWSGI app server
* A small NGINX configuration file wires the application to an external HTTP server and port.

It was quick to write applications that

* Take a JSON request and post it to a RabbitMQ message queue
* Calculate server process metrics and expose them at a given URL

These are indicative of the sort of simple apps this approach looks suited to. After examining the
Django WSGI integration code, it does not look difficult to support more advanced cases such as
streaming large responses.

This approach could prove valuable as we trend towards having larger numbers of smaller
applications hosted on servers, as a simple way of building small HTTP based applications
quickly and cleanly. For these reasons, it lends itself nicely to prototype and experimental
applications, and applications with limited lifespans. It is also a useful technique to support
integration with off-the-shelf software, given that current trends are towards web based software
that uses HTTP calls and APIs to handle custom integrations.

### Prometheus

https://prometheus.io/docs/introduction/overview/

Prometheus is a metrics server which

* Stores time series data for a number of different types of metric
* Handles metrics collection primarily by pulling them from URLs which expose those metrics
* Provides a rich query language for analysing the metrics
* Integrates a rules engine for firing alerts to Alertmanager based on those metrics

This is a very well built piece of software, focused and excellent at the task at hand, clearly
very capable in its field. The way that metrics are stored is logical, and the query language on
top of it is very powerful. It is designed to be installed on each **node** (i.e. server) that you
have, and handle gathering and storing metrics for that single node. You can also use Prometheus
for gathering metrics across a number of nodes, however the recommendation is that this only used
for collecting a small number of metrics that want to be compared across nodes, and not as a way
of centralizing metrics storage. Having played around with it, this makes sense, it feels more
logical to treat each node as a single entity, with its own metrics dashboard.

#### Gathering metrics

There are all sorts of metrics that you can gather, here are just a few examples:

* CPU, memory, hard disk, network etc. statistics for the server
* NGINX request times, latencies, response codes
* UWSGI requests (more detailed than NGINX)
* RabbitMQ, Memcached, Postgresql etc etc
* Application specific metrics using hand rolled metrics exporters.

Each set of metrics is added to Prometheus by configuring a metrics exporter. These are ready
made and available for a lot of popular software packages, and it is also quite simple to write
your own, which is important given that Google advises you need a combination of black-box and
white-box metrics for your applications to be able to effectively monitor them.

There are four types of metric, which are well summarised here:

https://prometheus.io/docs/concepts/metric_types/

Prometheus wants metrics to be re-usable, i.e. if you are using a metric to record the amount of
memory used in a process, the same metric (i.e. a metric with the same name) should be used for each
process you are tracking this for, making it easy to re-use things that query the metrics such
as dashboards and alert handling rules. To distinguish between the same metric being used for two
different processes (for example), Prometheus allows you to attach labels to metrics. These are
basically key/value pairs that allow richer information to be recorded on the base metric. Examples
of labels on metrics include:

* `api_http_requests_total` may have a status code label to differentiate number of requests that
  had different types of response (200, 404 etc).
* `process_cpu_seconds_total` may have a process name label to differentiate processes.

To really get a feel for how metrics are stored and how they work, you need to play with the
Prometheus user interface in the example code. There is also excellent documentation on best
practices for creating and naming your own metrics:

https://prometheus.io/docs/practices/naming/

There is one caveat on the exporters that are already available for things like UWSGI, RabbitMQ and
Memcached. These turned out to be quite hard to install (and in the scope of this experiment, I gave
up). To use these you would need to either put a lot of effort into getting these working, write
your own, or use Docker (which seemed to be the **easy** way to use them). As a side note, this is
something to keep an eye on, we may be moving towards a time where even if our own applications are
not utilising containers, we may need to start using container technologies for the installation of
other software packages, as this becomes the standard approach to packaging and distributing
software. This does not feel like a bad thing.

#### Viewing metrics

The best way to get a feel for the power of the metrics is to plot them. The Prometheus UI is
handy for basic exploring, plotting and debugging (as well as getting a general feel for what
Prometheus is doing), however you should fire up Grafana to really get a feel for their power.
It looks straightforward to hook into these metrics from other systems too using the Prometheus
API, however I did not try this out.

#### Raising alerts

Prometheus has a sophisticated system for raising alerts. We need to draw a clear distinction
here between Prometheus and Alertmanager. Prometheus simply handles the **firing** of alerts, and
Alertmanager decides what to do with them. Note that we assume that you are using Alertmanager to
handle alerts. Prometheus does not require you configure an alerts system, and may even be able to
hook into other alert handling systems although we did not try this out.

Alerts are configured individually in Prometheus using rules, where you provide the following for
each alert rule:

* A name for the alert
* An expression using the Prometheus query language to indicate when to fire the alert
* How long the alert needs to be active for before we fire it
* A dictionary of labels which are used to categorize alerts
* A dictionary of annotations which provide additional information

It is important to understand how Prometheus deals with firing alerts:

* All alert rules are frequently evaluated (the time between evaluations is configurable).
* When a rule is first matched (i.e. its expression returns true), the alert becomes pending.
* A rule has a length of time for which its expression must be true before it starts firing, and
  if the expression returns true every time it is evaluated for that period of time, the alert
  becomes active and begins firing. This is useful because, for example if you wanted to be
  alerted for high CPU usage, you could require the CPU usage to be high for 5 minutes before
  firing the alert, to avoid being alerted to temporary spikes. This time defaults to zero
  seconds, meaning an alert will fire as soon as the expression returns true.
* When an alert first begins firing, a message is sent to Alertmanager with details of the alert.
* After the alert begins firing, each time the alert rules are evaluated and the expression is still
  true, the alert is sent to Alertmanager again.
* Once the rule expression returns false, the alert becomes inactive and stops firing the alert
  to Alertmanager, and becomes inactive.

A single alert rule may have multiple active instances at the same time. For example, if we had
an alert rule to fire alerts when process memory usage was above 90%, and that matched for multiple
processes at the same time, then multiple separate active instances of the alert would be created.
If this can happen, you need to configure your alert to differentiate between the two, in this case
you would probably use the process name found in the metrics labels, and pass that through in the
alerts labels and/or annotations.

Having played around with this, it feels like an excellent way of dealing with raising alerts.
Defining rules is simple and incredibly powerful, and because of the way that Prometheus stores
metrics, should avoid most cases of duplication (i.e. one 'process memory usage too high' alert
should satisfy all processes being monitored). Furthermore, the fact that an alert has a lifespan,
only gets fired after you are certain there is a problem, and also automatically resolves itself
if the problem goes away, should mean that fewer alerts have to be looked into by support staff.

#### Summary

To summarise, Prometheus looks to be a tremendously powerful system for automating the storage
and use of metrics. It is very flexible, can cope with both general black-box and application
specific white-box metrics easily, supports both sophisticated alerting for automated
monitoring and notifying people of problems, and powerful dashboards for viewing and exploring
detailed system behaviour.

### Grafana

Grafana is a powerful dashboard based system that sits on top of Prometheus, along with other data
stores, and enables construction of dashboard based views of the (primarily time series based) data.
Talking about Grafana is a little pointless, you really need to play with it to get a good feel of
how good it is.

Some standout features of Grafana:

* Create multiple, complex dashboards on top of any data found in your data source, with the ability
  to use their entire expression language to gather the data.
* Very simple to change the time scales being displayed.
* Dashboards can be imported and exported using a JSON format.
* Loads of ready made dashboards online ready to be imported, including lots of examples built
  around the different Prometheus metrics exporters available online (e.g. in the example we were
  able to install a NGINX metrics exporter for Prometheus, and a ready made dashboard that would
  display these metrics in Grafana).

These last two points are really key when it comes to the usability of Grafana. If you had to make
all the dashboards from scratch, it would be a very steep learning curve for both dashboard
construction and learning how to create the relevant Prometheus queries. However, with the ability
to import ready made examples, tweak them and save their JSON for reloading later, you are able to
get going fairly quickly, as well as face a much shallower learning curve to understand the full
power of Grafana and Prometheus.

All in all, Grafana is a great partner to Prometheus, and looks ideally suited to hosting lots of
dashboards which become useful when exploring support issues, server performance and application
performance. However, it is a tool that requires user engagement, it is not able to tell you when
there are problems that you need to look at. That is the job of Alertmanager.

### Alertmanager

Alertmanager is a system that does one thing - handles alerts, with the core responsibility being
to send the right alerts to the right systems, notifying the right people when problems arise.
Typically, these alerts come from Prometheus, with each alert received containing:

* A set of labels, as key/value pairs, which categorise the alert
* A set of annotations, again key/value pairs, containing more free-form information such as a
  summary of the alert
* Optional start and end times for the alert, which are typically not provided, and therefore
  Alertmanager will infer the start and end times for an alert based on the timespan across which
  Prometheus is firing that alert.

The labels that end up in the alerts received are defined in the Prometheus alert rules, they
drive most of the key features in Alertmanager, and are used heavily for configuring the system.
Therefore, it is important that effort is put in to defining an effective schema for your alert
labels, and ensuring this is faithfully adhered to in your rules across both Prometheus and
Alertmanager. I suspect that this will require on-going attention, at least in the early days of
setting these systems up, to find an effective configuration.

So, there are a number of key functions that Alertmanager has:

* The routing tree, which makes decisions where alerts should go. The routing tree uses alert labels
  to select the path through the tree which each alert should take, and ultimately alerts may end
  up triggering one or more receivers. A receiver sends the alert somewhere, and there are a number
  of integrations such as Slack, HipChat, various sophisticated paging systems, along with a general
  webhook that can satisfy most bespoke needs.
* Alerts are grouped, again using labels, which means that you can receive multiple alerts and
  have them result in a single alert. There is a group wait parameter which means that, after the
  first alert for a group is received, it will wait that long until handling the alert. This gives
  a chance for other alerts that would be grouped with it to arrive.
* Once a group of alerts have been sent to their receiver/s, they will only be re-sent after a
  certain amount of time, known as the repeat interval, has elapsed.
* You can tell one type of alert to inhibit others. For example, if your web server is down, and
  this is going to cause all sorts of other alerts, you can configure the system to just notify
  the 'web server is down' alert and inhibit the rest until that alert is no longer active. This
  matches alerts using labels.
* Alerts can be silenced through the user interface, using labels to match alerts that need to be
  silenced, and naturally these will not be sent to receivers until the silencer is removed.

Overall, this looks like a highly capable set of functions for managing alerts, and like
Prometheus it strikes a nice balance between simplicity of configuration, flexibility and power.
However, it also becomes clear that collecting metrics, and using them effectively for alerting, is
not a case where you install some software and it all happens by magic. Effective use of these tools
will require

* A reasonable understanding of how Prometheus and Alertmanager work
* Some background reading in metrics best practices
* A clear idea of what issues you want to identify, and how this can be done using metrics
* A carefully built schema for alert label keys
* Continued refinement of alert rules in both Prometheus and Alertmanager

This is intended to serve as a reality check, not to put people off!

One final note, when rolling this out for real, I think you would want your receiver to be notified
when an alert _stopped_ firing, as well as when it started firing and any repeats (according to your
repeat interval). This would make it simpler for staff reviewing the alerts after a period where
there was no support coverage (i.e. overnight) to identify which ones were no longer active, and
more effectively prioritise any investigations. I believe (having seen this in a screen-shot
somewhere) that this happens with HipChat, but cannot be certain.

## Conclusion

(we are ignoring UWSGI)

Prometheus, Grafana and Alertmanager are an excellent set of tools that together can provide a
comprehensive, scalable solution for measuring, monitoring and inspecting your software systems.
The tools themselves, and the targeted feature set that each one has, feel like the hallmark of
software designed and written by people who were experts in their domain. They are well respected,
mature pieces of open source software, and I would happily use them in a production environment.

I would be inclined to deploy these software packages as follows:

* A central instance of Alertmanager that gathers and handles all alerts in a single location.
* Instances of Prometheus and Grafana on each server (node), to handle metrics both for that node
  and the software running on it, sending alerts to the centralised Alertmanager instance. Note that
  because the configuration for raising alerts happens in Prometheus, you will need to deploy
  alerts configuration changes to every server (and if this is not easy, look into Ansible).
* For larger software installations (i.e. hundreds of servers plus) you may want to look at (a)
  central instances of Prometheus calculating metrics across servers, and horizontally scaling
  instances of Alertmanager (which is very easy to do).

This research has focused very much on general, black-box metrics, however application specific
white-box metrics are also vitally important, which begs the question: Is this a good fit for
application specific metrics, and generating alerts off of the back of them? The example that came
to mind - applications that I work with alert us when a task running in our software finishes in an
error state. At first I struggled to understand, how would this fit into Prometheus/Alertmanager,
how should it handle notifying of instances of errors occurring? Towards the end of the research, it
became clear that I needed to re-frame the solution, and what this situation calls for is:

* Maintaining a metric that counts the number of tasks that finish in error
* Raising an alert each time this number increases

Suddenly, this becomes a very natural fit, and arguably we end up with a much better way of
measuring our task errors (for example, we now have a count of how many errors we have had which
clearly has re-use opportunities, or we could now do things like grouping of alerts to send a single
alert if we suddenly get multiple tasks going into error). There is an important lesson here,
adopting the approach to metrics and alerting that these systems follow will likely require a shift
in thinking for people more used to the 'detect error and send us a message' approach that is rather
common. I am fully convinced that the way Prometheus and Alertmanager handle this is far superior.

It is important to understand that installing and configuring this software alone will not
automatically give you an excellent set of monitoring and alerting systems. You are very much
buying into an ecosystem that will require on-going maintenance to remain effective, to

* Add new metrics, and configure new alerts, when rolling out new functionality
* Curation of the alert labels schema and alerts rules as your systems grow
* Introduction of new metrics exporters, and more alerts configuration, as you introduce new
  software packages such as caches, storage, application servers etc.

Furthermore, there is a level of sophistication and understanding required to be able to roll this
out effectively, there is most definitely an art to this. I would imagine that any software team
rolling this out would need someone to take on the mantle of subject matter expert and evangelist
to get this system up and running, and further work on their part to turn it into something that
can be managed by the group rather than an individual.

In conclusion, I am keen roll this software out in my own organization, as it will enable us to
better automate and scale our systems monitoring, alerting and support, and move towards more
intelligent monitoring of systems performance. However, before doing so, I would need to do a lot
more research into metrics best practices, and conduct a reasonable amount of analysis of our
current alerts and do some up-front planning for our alert labels schema.

## Further reading

* The best practices section (and indeed all of) https://prometheus.io/docs/
* A decent write-up of best practices regarding alerts:
  https://docs.google.com/document/d/199PqyG3UsyXlwieHaqbGiWVa8eMWi8zzAn0YfcApr8Q/edit
* The book 'Site Reliability Engineering - How Google Runs Production Systems'
