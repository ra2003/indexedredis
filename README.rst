IndexedRedis
============

A redis-backed very very fast ORM-style framework that supports indexes (similar to SQL).

Requires a Redis server of at least version 2.6.0, and python-redis [ available at https://pypi.python.org/pypi/redis ]

IndexedRedis supports both “equals” and "not-equals" operators for comparison. It also provides full atomic support for replacing entire datasets (based on model), which is useful for providing a fast frontend for SQL. In that use-case, a task that runs on an interval would fetch/calculate datasets from the SQL backend, and do an atomic replace on the datasets the front-end would query.

If you have ever used Flask or Django you will recognize strong similarities in the filtering interface. 

My tests have shown that for using equivalent models between flask/mysql and IndexedRedis, a 600% - 1200% performance increase occurs. For actually redesigning the system to prefetch and .reset (as mentioned above), response time went from ~3.5s per page load to ~20ms [ 17500% faster ].

It is compatible with python 2.7 and python 3. It has been tested with python 2.7 and 3.4.


API Reference
-------------

Most, but not all methods are documented here.

See: `This Page <http://htmlpreview.github.io/?https://github.com/kata198/indexedredis/blob/master/IndexedRedis.html#IndexedRedisQuery>`_ for full documentation as a pydoc document.


**Below is a quick highlight/overview**


IndexedRedisModel
-----------------

This is the model you should extend.

**Example Model:**

	class Song(IndexedRedisModel):
	    
		FIELDS = [ \
				'artist',
				'title',
				'album',
				'track_number',
				'duration',
				'description',
				'copyright',
		]

		INDEXED_FIELDS = [ \
					'artist',
					'title',
					'track_number',
		]

		KEY_NAME = 'Songs'


**Required Fields:**

*FIELDS* - a list of strings which name the fields that can be used for storage.

	 Example: ['Name', 'Description', 'Model', 'Price']

*INDEXED_FIELDS* -  a list of strings containing the names of fields that should be indexed. Every field listed here adds insert performance. To filter on a field, it must be in the INDEXED\_FIELDS list.

	 Example: ['Name', 'Price']

*KEY_NAME* - A unique name name that represents this model. Think of it like a table name.

	 Example 'Items'

*REDIS_CONNECTION_PARAMS* - provides the arguments to pass into "redis.Redis", to construct a redis object.

	 Example: {'host' : '192.168.1.1'}

Usage
-----

Usage is very similar to Django or Flask

**Query:**

Calling .filter or .filterInline builds a query/filter set. Use one of the *Fetch* methods described below to execute a query.

	objects = SomeModel.objects.filter(param1=val).filter(param2=val).all()

**Save:**
	obj = SomeModel(field1='value', field2='value')
	obj.save()

**Delete Using Filters:**
	SomeModel.objects.filter(name='Bad Man').delete()

**Delete Individual Objects:**

	obj.delete()


**Atomic Dataset Replacement:**

There is also a powerful method called "reset" which will **atomically** replace all elements belonging to a model. This is useful for cache-replacement, etc.

	lst = [SomeModel(...), SomeModel(..)]

	SomeModel.reset(lst)

For example, you could have a SQL backend and a cron job that does complex queries (or just fetches the same models) and does an atomic replace every 5 minutes to get massive performance boosts in your application.

Filter objects by SomeModel.objects.filter(key=val, key2=val2) and get objects with .all

Example: SomeModel.objects.filter(name='Tim', colour='purple').filter(number=5).all()


**Fetch Functions**:

Building filtersets do not actually fetch any data until one of these are called (see API for a complete list). All of these functions act on current filterset.

Example: matchingObjects = SomeModel.objects.filter(...).all()

	all    - Return all objects matching this filter

	allOnlyFields - Takes a list of fields and only fetches those fields, using current filterset

	delete - Delete objects matching this filter

	count  - Get the count of objects matching this filter

	first  - Get the oldest record with current filters

	last   - Get the newest record with current filters

	random - Get a random element with current filters

	getPrimaryKeys - Gets primary keys associated with current filters


**Filter Functions**

These functions add filters to the current set. "filter" returns a copy, "filterInline" acts on that object.

	filter - Add additional filters, returning a copy of the filter object (moreFiltered = filtered.filter(key2=val2))

	filterInline - Add additional filters to current filter object. 


**Global Fetch functions**

These functions are available on SomeModel.objects and don't use any filters (they get specific objects):

	get - Get a single object by pk

	getMultiple - Get multiple objects by a list of pks


**Model Functions**

Actual objects contain methods including:

	save   - Save this object (create if not exist, otherwise update)

	delete - Delete this object

	getUpdatedFields - See changes since last fetch




Encodings
---------

IndexedRedis will use by default your system default encoding (sys.getdefaultencoding), unless it is ascii (python2) in which case it will default to utf-8.

You may change this via IndexedRedis.setEncoding

Changes
-------

See `Changelog <https:////raw.githubusercontent.com/kata198/indexedredis/master/Changelog>`_ for list of changes.

Example
-------

See `This Example <https:////raw.githubusercontent.com/kata198/indexedredis/master/test.py>`_ for a working example.


Contact Me
----------

Please e-mail me with any questions, bugs, or even just to tell me that you're using it! kata198@gmail.com