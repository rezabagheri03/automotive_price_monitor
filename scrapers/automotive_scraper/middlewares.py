"""
Scrapy middlewares for automotive scraper
"""
import random
import logging
from urllib.parse import urlparse
from fake_useragent import UserAgent
from scrapy.downloadermiddlewares.retry import RetryMiddleware
from scrapy.downloadermiddlewares.httpproxy import HttpProxyMiddleware
from scrapy.utils.response import response_status_message
from scrapy.exceptions import NotConfigured
from config.settings import Config

logger = logging.getLogger(__name__)


class UserAgentMiddleware:
    """Rotate User-Agent headers"""
    
    def __init__(self):
        self.ua = UserAgent()
        self.config = Config()
        
        # Predefined user agents for Iranian sites
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:89.0) Gecko/20100101 Firefox/89.0',
            'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:89.0) Gecko/20100101 Firefox/89.0',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Edge/91.0.864.59',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15'
        ]
    
    def process_request(self, request, spider):
        """Set random user agent for request"""
        if self.config.USER_AGENT_ROTATION:
            try:
                # Use fake_useragent for random UA
                user_agent = self.ua.random
            except:
                # Fallback to predefined list
                user_agent = random.choice(self.user_agents)
        else:
            user_agent = random.choice(self.user_agents)
            
        request.headers['User-Agent'] = user_agent
        return None


class ProxyMiddleware:
    """Handle proxy rotation"""
    
    def __init__(self):
        self.config = Config()
        self.proxies = []
        
        if self.config.PROXY_ENABLED and self.config.PROXY_LIST:
            self.proxies = [proxy.strip() for proxy in self.config.PROXY_LIST if proxy.strip()]
            logger.info(f"Loaded {len(self.proxies)} proxies")
        else:
            logger.info("Proxy rotation disabled")
    
    def process_request(self, request, spider):
        """Set random proxy for request"""
        if not self.proxies:
            return None
            
        proxy = random.choice(self.proxies)
        
        # Handle proxy with authentication
        if self.config.PROXY_AUTH:
            auth = self.config.PROXY_AUTH
            request.meta['proxy'] = f"http://{auth}@{proxy}"
        else:
            request.meta['proxy'] = f"http://{proxy}"
            
        logger.debug(f"Using proxy: {proxy}")
        return None


class CustomRetryMiddleware(RetryMiddleware):
    """Custom retry middleware with enhanced logic"""
    
    def __init__(self, settings):
        super().__init__(settings)
        self.max_retry_times = settings.getint('RETRY_TIMES', 3)
        self.retry_http_codes = set(int(x) for x in settings.getlist('RETRY_HTTP_CODES'))
        self.priority_adjust = settings.getint('RETRY_PRIORITY_ADJUST', -1)
        
    def process_response(self, request, response, spider):
        """Process response and retry if needed"""
        if request.meta.get('dont_retry', False):
            return response
            
        if response.status in self.retry_http_codes:
            reason = response_status_message(response.status)
            return self._retry(request, reason, spider) or response
            
        return response
    
    def process_exception(self, request, exception, spider):
        """Process exception and retry if needed"""
        if (
            isinstance(exception, self.EXCEPTIONS_TO_RETRY)
            and not request.meta.get('dont_retry', False)
        ):
            return self._retry(request, exception, spider)


class HeadersMiddleware:
    """Add custom headers for Iranian sites"""
    
    def __init__(self):
        self.headers = {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'fa-IR,fa;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none'
        }
    
    def process_request(self, request, spider):
        """Add custom headers to request"""
        for header, value in self.headers.items():
            if header not in request.headers:
                request.headers[header] = value
        
        # Add site-specific headers
        domain = urlparse(request.url).netloc
        if 'iran' in domain or '.ir' in domain:
            request.headers['Accept-Language'] = 'fa-IR,fa;q=0.9,en;q=0.8'
        
        return None


class DelayMiddleware:
    """Custom delay middleware for different sites"""
    
    def __init__(self, settings):
        self.default_delay = settings.getfloat('DOWNLOAD_DELAY', 1)
        self.randomize = settings.getfloat('RANDOMIZE_DOWNLOAD_DELAY', 0.5)
        
        # Site-specific delays from config
        self.site_delays = getattr(settings, 'IRANIAN_SITES_CONFIG', {})
    
    @classmethod
    def from_crawler(cls, crawler):
        return cls(crawler.settings)
    
    def process_request(self, request, spider):
        """Apply site-specific delays"""
        domain = urlparse(request.url).netloc
        
        # Check if we have custom delay for this domain
        for site, config in self.site_delays.items():
            if site in domain:
                delay = config.get('delay', self.default_delay)
                break
        else:
            delay = self.default_delay
        
        # Add randomization
        if self.randomize:
            delay += random.uniform(0, self.randomize)
        
        # Set delay in spider
        if hasattr(spider, 'download_delay'):
            spider.download_delay = delay
            
        return None


class StatsMiddleware:
    """Collect custom statistics"""
    
    def __init__(self, stats):
        self.stats = stats
    
    @classmethod
    def from_crawler(cls, crawler):
        return cls(crawler.stats)
    
    def process_request(self, request, spider):
        """Track request statistics"""
        self.stats.inc_value('custom/requests_total')
        
        domain = urlparse(request.url).netloc
        self.stats.inc_value(f'custom/requests_per_domain/{domain}')
        
        return None
    
    def process_response(self, request, response, spider):
        """Track response statistics"""
        self.stats.inc_value('custom/responses_total')
        self.stats.inc_value(f'custom/responses_status/{response.status}')
        
        return response
