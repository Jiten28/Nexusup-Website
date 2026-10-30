"""Bounded HTTPS client: public-IP pinning, TLS hostname verification, redirect checks."""
import ipaddress, socket, json
from http.client import HTTPSConnection
from urllib.parse import urlsplit
from urllib.request import Request, build_opener, HTTPRedirectHandler, HTTPSHandler, ProxyHandler


def public_addresses(host, port=443):
    addresses=socket.getaddrinfo(host,port,type=socket.SOCK_STREAM)
    if not addresses or any(not ipaddress.ip_address(item[4][0]).is_global for item in addresses):
        raise ValueError('Non-public network destinations are blocked.')
    return addresses


def validate_url(url):
    parts=urlsplit(url)
    if parts.scheme!='https' or not parts.hostname or parts.username or parts.password or parts.port not in (None,443):
        raise ValueError('Only public HTTPS URLs on port 443 are accepted.')
    public_addresses(parts.hostname)
    return url


def pinned_connection(address, timeout=8, source_address=None):
    # Resolve once at connection time, validate ALL answers, then connect by numeric IP.
    # HTTPSConnection still verifies the original hostname and uses it for TLS SNI.
    addresses=public_addresses(address[0],address[1])
    last=None
    for family,socktype,proto,_,sockaddr in addresses:
        sock=socket.socket(family,socktype,proto)
        try:
            sock.settimeout(timeout)
            if source_address: sock.bind(source_address)
            sock.connect(sockaddr)
            return sock
        except OSError as exc:
            last=exc; sock.close()
    raise last or OSError('No public destination available')


class PublicHTTPSConnection(HTTPSConnection):
    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs)
        self._create_connection=pinned_connection


class PublicHTTPSHandler(HTTPSHandler):
    def https_open(self,req):
        return self.do_open(PublicHTTPSConnection,req,context=self._context)


class SafeRedirect(HTTPRedirectHandler):
    def redirect_request(self,req,fp,code,msg,headers,newurl):
        validate_url(newurl)
        old_host=urlsplit(req.full_url).hostname
        new_host=urlsplit(newurl).hostname
        if old_host != new_host and any(req.has_header(name) for name in ('Authorization','X-api-key','X-Api-Key')):
            raise ValueError('Cross-host redirects with credentials are blocked.')
        return super().redirect_request(req,fp,code,msg,headers,newurl)


def _fetch_bytes(url,data=None,max_bytes=2_000_000,headers=None,timeout=8):
    validate_url(url)
    request_headers={'User-Agent':'NexusUpFeedReader/1.0 (+editorial RSS metadata only)','Accept':'application/rss+xml,application/atom+xml,application/json,text/xml;q=0.9'}
    request_headers.update(headers or {})
    if data is not None: request_headers['Content-Type']='application/json'
    req=Request(url,data=json.dumps(data).encode() if data is not None else None,headers=request_headers)
    # Do not inherit environment proxies that could bypass destination validation.
    with build_opener(ProxyHandler({}),SafeRedirect(),PublicHTTPSHandler()).open(req,timeout=timeout) as response:
        body=response.read(max_bytes+1)
        if len(body)>max_bytes: raise ValueError('Response exceeded size limit.')
        return body


def fetch_bytes(url,data=None,max_bytes=2_000_000,headers=None,timeout=8):
    # Bounded retries for transient GET failures only. Respect provider rate limiting;
    # HTTP 429 is not retried here and the source interval remains in force.
    import time
    from urllib.error import HTTPError, URLError
    for attempt in range(3):
        try: return _fetch_bytes(url,data=data,max_bytes=max_bytes,headers=headers,timeout=timeout)
        except HTTPError as exc:
            if data is not None or exc.code not in (502,503,504) or attempt==2: raise
        except (URLError,TimeoutError,OSError):
            if data is not None or attempt==2: raise
        time.sleep(2**attempt)

def fetch_json(url,data=None,headers=None,timeout=8):
    return json.loads(fetch_bytes(url,data=data,headers=headers,timeout=timeout))
