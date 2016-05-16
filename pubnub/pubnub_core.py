import logging
from abc import ABCMeta, abstractmethod

import requests
from requests import ConnectionError
from requests.packages.urllib3.exceptions import HTTPError

from .enums import HttpMethod
from .endpoints.pubsub.publish import Publish
from .endpoints.presence.herenow import HereNow
from .structures import RequestOptions
from .exceptions import PubNubException
from .errors import PNERR_CLIENT_TIMEOUT, PNERR_HTTP_ERROR, PNERR_CONNECTION_ERROR, PNERR_TOO_MANY_REDIRECTS_ERROR, \
    PNERR_SERVER_ERROR, PNERR_CLIENT_ERROR, PNERR_UNKNOWN_ERROR


logger = logging.getLogger("pubnub")


class PubNubCore:
    """A base class for PubNub Python API implementations"""
    SDK_VERSION = "4.0.0"
    SDK_NAME = "PubNub-Python"

    __metaclass__ = ABCMeta

    def __init__(self, config):
        self.config = config
        self.session = requests.Session()

        self.config.validate()

    def request_sync(self, options):
        assert isinstance(options, RequestOptions)

        url = self.config.scheme_and_host() + options.path
        method = HttpMethod.string(options.method)
        logger.debug("%s %s %s" % (method, url, options.params))

        # connection error
        try:
            res = self.session.request(method, url, params=options.params)
        except ConnectionError as e:
            raise PubNubException(
                pn_error=PNERR_CONNECTION_ERROR,
                errormsg=str(e)
            )
        except HTTPError as e:
            raise PubNubException(
                pn_error=PNERR_HTTP_ERROR,
                errormsg=str(e)
            )
        except requests.exceptions.Timeout as e:
            raise PubNubException(
                pn_error=PNERR_CLIENT_TIMEOUT,
                errormsg=str(e)
            )
        except requests.exceptions.TooManyRedirects as e:
            raise PubNubException(
                pn_error=PNERR_TOO_MANY_REDIRECTS_ERROR,
                errormsg=str(e)
            )
        except Exception as e:
            raise PubNubException(
                pn_error=PNERR_UNKNOWN_ERROR,
                errormsg=str(e)
            )

        # http error
        if res.status_code != requests.codes.ok:
            if res.text is None:
                text = "N/A"
            else:
                text = res.text

            if res.status_code >= 500:
                err = PNERR_SERVER_ERROR
            else:
                err = PNERR_CLIENT_ERROR

            raise PubNubException(
                pn_error=err,
                errormsg=text,
                status_code=res.status_code
            )

        return res.json()

    @abstractmethod
    def request_async(self, options, success, error):
        pass

    @abstractmethod
    def request_deferred(self, options_func):
        pass

    def here_now(self):
        return HereNow(self)

    def publish(self):
        return Publish(self)

    @property
    def sdk_name(self):
        return "%s%s/%s" % (PubNubCore.SDK_NAME, self.sdk_platform(), PubNubCore.SDK_VERSION)

    @abstractmethod
    def sdk_platform(self): pass

    @property
    def uuid(self):
        return self.config.uuid
