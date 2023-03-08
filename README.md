# Python memoize decorator

The class provided in this repository can be imported into your project and used as a decorator 
for any method. It has the ability to cache the output of a function provided that the
method takes at least one argument (read: argument, not keyword argument!). The _first_
argument is used as a key for storing the cache into a dictionary. 

### Example usage:

Let's assume we're dealing with a django-view file where a user can look up students
by year of registration and see how many students are signed in.

    from Memoize import Memoize

    memoize = Memoize(ttl=300, max_items=100)

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
    def signed_in(building):
          query = {'building': building}
          _students = list(SignedIn.objects.objects.filter(**query).all())
          ...
          return result

In above example you can use the memoize decorator with a predefined `ttl` in seconds or override
the `ttl` for a specific use case.

### Behaviour

- When the `ttl` has expired for a cached item, the cache is invalid and will be cleared on next call.
- When the amount of items exceeds the `max_items`, items with will be purged by ttl until `max_items` are
  present in the cache
- `ttl` can be overriden for a specific use case by setting the `ttl` in the decorator as a `kwarg`
- `max_items` and `ttl` are set to a chosen value on class initialization, when omitted they default to
  `ttl:` 300 seconds and `max_items:` 128 items. 

### Dependencies

Memoize depends on the python build-ins `time` and `functools`

