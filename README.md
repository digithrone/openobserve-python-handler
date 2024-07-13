# The OpenObserve Python Handler

<table><tr><th>
</th></tr></table>

Disclaimer: This project is based on https://github.com/logzio/logzio-python-handler/ code snapshot taken on 15.2.2024.

This is a Python handler that sends logs in bulk over HTTPS to OpenObserve service.
The handler uses a subclass named OpenObserveSender (which can be used without this handler as well, to ship raw data).
The OpenObserveSender class opens a new Thread, that consumes from the logs queue. Each iteration (its frequency of which can be configured by the logs_drain_timeout parameter), will try to consume the queue in its entirety.
Logs will get divided into separate bulks, based on their size.
OpenObserveSender will check if the main thread is alive. In case the main thread quits, it will try to consume the queue one last time, and then exit. So your program can hang for a few seconds, until the logs are drained.
In case the logs failed to be sent to OpenObserve service after a couple of tries, they will be written to the local file system. You can later upload them to OpenObserve using curl.


## Installation
```bash
pip install openobserve-python-handler
```

## Tested Python Versions
Travis CI will build this handler and test against:
  - "3.11"

We can't ensure compatibility to any other version, as we can't test it automatically.

To run tests:

```bash
$ pip install tox
$ tox
...

```

## Python configuration
#### Config File
```python
[handlers]
keys=OpenObserveHandler

[handler_OpenObserveHandler]
class=openobserve.handler.OpenObserveHandler
formatter=openobserveFormat

# Parameters must be set in order. Replace these parameters with your configuration.
args=('<<LOG-USERNAME>>','<<LOG-PASSWORD>>','<<LOG-URL>>','<<LOG-ORGANIZATION>>','<<LOG-STREAM>>', '<<LOG-TYPE>>', <<TIMEOUT>>, <<DEBUG-FLAG>>,<<NETWORKING-TIMEOUT>>,<<RETRY-LIMIT>>,<<RETRY-TIMEOUT>>)

[formatters]
keys=openobserveFormat

[loggers]
keys=root

[logger_root]
handlers=OpenObserveHandler
level=INFO

[formatter_openobserveFormat]
format={"additional_field": "value"}
```
*args=() arguments, by order*
 - OpenObserve username
 - OpenObserve password
 - OpenObserve Listener address (i.e. to "https://openobserve.mydomain.net")
 - OpenObserve organization (i.e. to "myorg")
 - OpenObserve stream (i.e. "mystream")
 - Log type, for searching in OpenObserve (defaults to "python")
 - Time to sleep between draining attempts (defaults to "3")
 - Debug flag. Set to True, will print debug messages to stdout. (defaults to "False")
 - Backup logs flag. Set to False, will disable the local backup of logs in case of failure. (defaults to "True")
 - Network timeout, in seconds, int or float, for sending the logs to OpenObserve. (defaults to 10)
 - Retries number (retry_no, defaults to 4).
 - Retry timeout (retry_timeout) in seconds (defaults to 2).

 Please note, that you have to configure those parameters by this exact order.
 i.e. you cannot set Debug to true, without configuring all of the previous parameters as well.

#### Dict Config
```python
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'openobserveFormat': {
            'format': '{"additional_field": "value"}',
            'validate': False
        }
    },
    'handlers': {
        'openobserve': {
            "username": '<<OPENOBSERVE-USERNAME>>',
            "password": '<<OPENOBSERVE-PASSWORD>>',
            'url': '<<OPENOBSERVE-URL>>',
            "organization": '<<OPENOBSERVE-ORGANIZATION>>',
            "stream": '<<OPENOBSERVE-STREAM>>',
            'class': 'openobserve.handler.OpenObserveHandler',
            'level': 'INFO',
            'formatter': 'openobserveFormat',
            'openobserve_type': 'python-handler',
            'logs_drain_timeout': 5,
            'retries_no': 4,
            'retry_timeout': 2,
        }
    },
    'loggers': {
        '': {
            'level': 'DEBUG',
            'handlers': ['openobserve'],
            'propagate': True
        }
    }
}
```
Replace:
* <<OPENOBSERVE-USERNAME>> - OpenObserve username
* <<OPENOBSERVE-PASSWORD>> - OpenObserve password
* <<OPENOBSERVE-URL>> - OpenObserve listener service i.e. http://localhost:5080
* <<OPENOBSERVE-ORGANIZATION>> - OpenObserve organization i.e. "myorg"
* <<OPENOBSERVE-STREAM>> - OpenObserve stream i.e my stream

#### Dynamic Extra Fields
If you prefer, you can add extra fields to your logs dynamically, and not pre-defining them in the configuration.
This way, you can allow different logs to have different extra fields.
Example in the code below.

#### Code Example

```python
import logging
import logging.config
# If you're using a serverless function, uncomment.
# from openobserve.flusher import OpenObserveFlusher

# If you'd like to leverage the dynamic extra fields feature, uncomment.
# from openobserve.handler import ExtraFieldsLogFilter

# Say I have saved my configuration as a dictionary in a variable named 'LOGGING' - see 'Dict Config' sample section
logging.config.dictConfig(LOGGING)
logger = logging.getLogger('superAwesomeOpenObserveLogger')

# If you're using a serverless function, uncomment.
# @OpenObserveFlusher(logger)
def my_func():
    logger.info('Test log')
    logger.warn('Warning')

    try:
        1/0
    except:
        logger.exception("Supporting exceptions too!")

# Example additional code that demonstrates how to dynamically add/remove fields within the code, make sure class is imported.

    logger.info("Test log")  # Outputs: {"message":"Test log"}

    extra_fields = {"foo":"bar","counter":1}
    logger.addFilter(ExtraFieldsLogFilter(extra_fields))
    logger.warning("Warning test log")  # Outputs: {"message":"Warning test log","foo":"bar","counter":1}

    error_fields = {"err_msg":"Failed to run due to exception.","status_code":500}
    logger.addFilter(ExtraFieldsLogFilter(error_fields))
    logger.error("Error test log")  # Outputs: {"message":"Error test log","foo":"bar","counter":1,"err_msg":"Failed to run due to exception.","status_code":500}

    # If you'd like to remove filters from future logs using the logger.removeFilter option:
    logger.removeFilter(ExtraFieldsLogFilter(error_fields))
    logger.debug("Debug test log") # Outputs: {"message":"Debug test log","foo":"bar","counter":1}

```

#### Extra Fields
In case you need to dynamic metadata to a speific log and not [dynamically to the logger](#dynamic-extra-fields), other than the constant metadata from the formatter, you can use the "extra" parameter.
All key values in the dictionary passed in "extra" will be presented in OpenObserve as new fields in the log you are sending.
Please note, that you cannot override default fields by the python logger (i.e. lineno, thread, etc..)
For example:

```python
logger.info('Warning', extra={'extra_key':'extra_value'})
```

#### Trace context

If you're sending traces with OpenTelemetry instrumentation (auto or manual), you can correlate your logs with the trace context.
That way, your logs will have traces data in it, such as service name, span id and trace id.

OpenTelemetry logging instrumentation is enabled by default.
To enable this feature, set the `add_context` param in your handler configuration to `True`, like in this example:

```python
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'openobserveFormat': {
            'format': '{"additional_field": "value"}',
            'validate': False
        }
    },
    'handlers': {
        'openobserve': {
            "username": '<<OPENOBSERVE-USERNAME>>',
            "password": '<<OPENOBSERVE-PASSWORD>>',
            'url': '<<OPENOBSERVE-URL>>',
            "organization": '<<OPENOBSERVE-ORGANIZATION>>',
            "stream": '<<OPENOBSERVE-STREAM>>',
            'class': 'openobserve.handler.OpenObserveHandler',
            'level': 'INFO',
            'formatter': 'openobserveFormat',
            'openobserve_type': 'python-handler',
            'logs_drain_timeout': 5,
            'retries_no': 4,
            'retry_timeout': 2,
            'add_context': True
        }
    },
    'loggers': {
        '': {
            'level': 'DEBUG',
            'handlers': ['openobserve'],
            'propagate': True
        }
    }
}
```

#### Django configuration
```python
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '%(levelname)s %(asctime)s %(module)s %(process)d %(thread)d %(message)s'
        },
        'openobserveFormat': {
            'format': '{"additional_field": "value"}',
            'validate': False
        }
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'level': 'DEBUG',
            'formatter': 'verbose'
        },
        'openobserve': {
            'class': 'openobserve.handler.OpenObserveHandler',
            'level': 'INFO',
            'formatter': 'openobserveFormat',
            'token': 'token',
            'openobserve_type': "django",
            'logs_drain_timeout': 5,
            'url': 'https://openobserver.mydomain.net',
            'debug': True,
            'network_timeout': 10,
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console', ],
            'level': os.getenv('DJANGO_LOG_LEVEL', 'INFO')
        },
        'appname': {
            'handlers': ['console', 'openobserve'],
            'level': 'INFO'
        }
    }
}

```


## Release Notes
- 1.0.2 - updated open telemetry reference as options to prevent collisions
- 0.9.0 - snapshot from https://github.com/logzio/logzio-python-handler/ taken on 15.2.2024 and then refactored and tested with openobserve
