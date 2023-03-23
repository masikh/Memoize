"""
    Python memoize decorator

    License: https://github.com/masikh/Memoize is licensed under the GNU General Public License v3.0

    Introduction:

    The class provided in this repository can be imported into your project and used as a decorator
    for any method. It has the ability to cache the output of a function provided that the
    method takes at least one argument (read: argument, not keyword argument!). There are three methods for creating
    a key for storing cache. These are 'args', 'request' and callable(function).

    Key strategies:

    The 'args' key strategy takes the arguments of the called function and creates a MD5 hash for a key. Only arguments
    of type string, list, boolean, integer and float are taken into consideration.

    The 'request' key strategy is used for APIs where the query-parameters of a API request are used to create a MD5
    hash for a key. A 'CACHE-CONTROL' header set with the value 'no-cache' indicates the memoization class to clear the
    cache for the returned key.

    The 'callable(function)' takes a privately made function to create a key. The function must return a tuple
    (key, cache_control) where 'key' is the key for storing the memoized function its result and 'cache_control' is
    either None or 'no-cache'. The cache_control is used to indicate the memoization class to clear the cache for the
    returned key.

    Cache-control:

    The cache can be cleared for a key in a few different ways but they are not all thread-save.

    - Set the 'clear_cache_key' class object to 'True'. This indicates that the next call to the memoize class will
      clear the cache for the key derived during that call. (Not thread-save)

    - By sending a 'CACHE-CONTROL' header set with the value 'no-cache' indicates the memoization class to clear the
      cache for the returned key. (thread-save)

    - By returning the value 'no-cache' for the 'cache-control' parameter in the returned tuple of a private
      key generator aka 'callable(function)' (thread-save)

    TTL:

    The 'ttl' of a cached item can be set globally in initialisation of the Memoize class (ttl=int), or overriden for a
    specific method by setting the 'ttl=int' parameter in the decorator. The value of the 'ttl' is in seconds. The 'ttl'
    of a cached item will not be renewed on a cache hit. When the `ttl` has expired for a cached item, the cache is
    invalid and will be cleared on next call.

    Max items:

    The 'max_items=int' parameter is used to limit the amount of cached items. If the cache limit is reached, new items
    will still be added by removing the oldest items from the cache.

    Dependencies:

    Memoize depends on the python build-ins `time`, `functools` and 'hashlib'

    Example usage:

    Let's assume we're dealing with a django-view file where a user can look up students
    by year of registration and see how many students there are present in the building.

    from Memoize import Memoize

    memoize = Memoize(ttl=300, max_items=100, key_strategy='args')

    @api_view(['GET'])
    @memoize
    def students(year, age=None):
        query = {'year': year}
        if age:
            query['age'] = age
        _students = list(Student.objects.objects.filter(**query).all())
        ...
        return Response(result)

    @api_view(['GET'])
    @memoize(ttl=5)
    def in_classroom(building):
        query = {'building': building}
        _students = list(InClassRoom.objects.objects.filter(**query).all())
        ...
        return Response(result)

    In above example you can use the memoize decorator with a predefined `ttl` in seconds or override
    the `ttl` for a specific use case.

    def my_key_generator(*args, **kwargs):
        return 'my key', None

    @memoize(ttl=5, key_generator=my_key_generator)
    def in_classroom(building):
        query = {'building': building}
        _students = list(InClassRoom.objects.objects.filter(**query).all())
        ...
        return Response(result)

    In this example the build-in key_generator 'args' set during initialization is omitted in favour of your own
    'my_key_generator' callable.
"""
import time
import functools
import hashlib


class Memoize:
    """
    Example usage:

        memoize = Memoize(ttl=300, max_items=100, key_strategy='args')

        @memoize
        def students(year, age=None):
            query = {'year': year}
            if age:
                query['age'] = age
            _students = list(Student.objects.objects.filter(**query).all())
            ...
            return result

        @memoize(ttl=5)
        def signed_in(building):
            query = {'building': building}
            _students = list(SignedIn.objects.objects.filter(**query).all())
            ...
            return result
    """

    def __init__(self, ttl=None, max_items=None, key_strategy=None):
        """ Set up the memoization parameters used during its live-time """
        self.memoize_cache = {}
        self.ttl = ttl if ttl is not None else 300
        self.max_items = max_items if max_items is not None else 128
        self.key_strategy = key_strategy if key_strategy is not None else 'args'
        self._key_strategy = None
        self.clear_cache_key = False

    def add_cache(self, key, value, ttl):
        """ Add items to the cache by key and add a ttl """
        self.memoize_cache[key] = (time.time() + ttl, value)

    def clean_cache(self):
        """ Remove items by time """
        now = time.time()
        self.memoize_cache = {key: value for key, value in self.memoize_cache.items() if now <= value[0]}

        # Remove all items more than self.max_items by cache-age
        sorted_cache = sorted(self.memoize_cache.items(), key=lambda x: x[1][0], reverse=False)
        for key, value in sorted_cache:
            if len(self.memoize_cache) - self.max_items <= 0:
                break
            del self.memoize_cache[key]

    def generate_key(self, *args, **kwargs):
        """ Generate a key for lookup or storing into the cache by key strategy """
        key = None
        cache_control = None

        if self._key_strategy == 'args':
            # Concatenate the values of all other keys into a single string
            values_string = ''.join(str(v) for v in args if isinstance(v, (str, list, int, float)))

            # Compute the MD5 hash of the string
            key = hashlib.md5(values_string.encode()).hexdigest()
            cache_control = 'no-cache' if self.clear_cache_key else None

        if self._key_strategy == 'request':
            # Concatenate the query parameters from the request and create a key
            request = args[0]
            cache_control = request.META.get('HTTP_CACHE-CONTROL', None)
            query_params = request.query_params

            # Define the pagination keys
            pagination_keys = ['page', 'page_size']

            # Concatenate the values of all other keys into a single string
            values_string = ''.join(str(v) for k, v in query_params.items() if k not in pagination_keys)

            # Compute the MD5 hash of the string
            key = hashlib.md5(values_string.encode()).hexdigest()

        if callable(self._key_strategy):
            # Use your own key strategy function. It must return a key and cache_control (None or 'no-cache')
            key, cache_control = self._key_strategy()

        self.clear_cache_key = False  # Set back to false for next request
        return key, cache_control

    def __call__(self, func=None, ttl=None, key_strategy=None):
        """ Main entry point """
        if func is None:
            return functools.partial(self.__call__, ttl=ttl, key_strategy=key_strategy)

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Set ttl for this cache item
            _ttl = self.ttl if ttl is None else ttl
            self._key_strategy = self.key_strategy if key_strategy is None else key_strategy

            # Generate cache key
            key, cache_control = self.generate_key(*args, **kwargs)

            # Client requests to clear cache
            if cache_control == 'no-cache':
                self.memoize_cache.pop(key, None)

            # Check if key in cache
            if key in self.memoize_cache:
                # if key is not expired, return result
                if time.time() - self.memoize_cache[key][0] <= _ttl:
                    result = self.memoize_cache[key][1]
                    self.clean_cache()
                    return result

                # Remove expired key
                del self.memoize_cache[key]

            # Cache miss, execute the function and fill the cache
            result = func(*args, **kwargs)
            if key is not None:
                self.add_cache(key, result, _ttl)
            self.clean_cache()
            return result

        return wrapper
