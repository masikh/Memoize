# Python memoize decorator

### Copyright:

https://github.com/masikh/Memoize is licensed under the GNU General Public License v3.0

Permissions of this strong copyleft license are conditioned on making available complete source code of licensed
works and modifications, which include larger works using a licensed work, under the same license. Copyright and
license notices must be preserved. Contributors provide an express grant of patent rights.

### Introduction:

The class provided in this repository can be imported into your project and used as a decorator
for any method. It has the ability to cache the output of a function provided that the
method takes at least one argument (read: argument, not keyword argument!). There are three methods for creating
a key for storing cache. These are 'args', 'request' and callable(function).

#### Key strategies:

There are two build-in key generators and if needed you can provide your own key generator via a callable object. 

- The 'args' key strategy takes the arguments of the called function and creates a MD5 hash for a key. Only arguments
of type string, list, boolean, integer and float are taken into consideration.

- The 'request' key strategy is used for APIs where the query-parameters of a API request are used to create a MD5
hash for a key. A 'CACHE-CONTROL' header set with the value 'no-cache' indicates the memoization class to clear the
cache for the returned key.

- The 'callable(function)' takes a privately made function to create a key. The function must return a tuple
(key, cache_control) where 'key' is the key for storing the memoized function its result and 'cache_control' is
either None or 'no-cache'. The cache_control is used to indicate the memoization class to clear the cache for the
returned key.

#### Cache-control:

The cache can be cleared for a key in a few different ways, but not all are thread-save!

- Set the 'clear_cache_key' class object to 'True'. This indicates that the next call to the memoize class will
  clear the cache for the key derived during that call. (Not thread-save)

- By sending a 'CACHE-CONTROL' header set with the value 'no-cache' indicates the memoization class to clear the
  cache for the returned key. This can be used with the 'request' key-strategy (thread-save)

- By returning the value 'no-cache' for the 'cache-control' parameter in the returned tuple of a private
  key generator aka 'callable(function)' (thread-save)

#### TTL:

The 'ttl' of a cached item can be set globally in initialisation of the Memoize class (ttl=int), or overriden for a
specific method by setting the 'ttl=int' parameter in the decorator. The value of the 'ttl' is in seconds. The 'ttl'
of a cached item will not be renewed on a cache hit. When the `ttl` has expired for a cached item, the cache is
invalid and will be cleared on next call.

#### Max items:

The 'max_items=int' parameter is used to limit the amount of cached items. If the cache limit is reached, new items
will still be added by removing the oldest items from the cache.

#### Dependencies:

Memoize depends on the python build-ins `time`, `functools` and 'hashlib'

#### Example usage:

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
