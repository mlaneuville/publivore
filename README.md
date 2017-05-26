publivore
=========

Description
-----------

Publivore is a python tool to monitor new research articles.

Content
-------

* main.cfg has the list of journal urls
* retrieve.py populate the database
* view.py helps to search the database and find interesting idx
* update.py stores likes in user database from idx
* analysis.py shows list of likes and suggest recommended papers
* serve.py starts a flask application
* publivore.yml is a conda environment file

Webapp
------

Only `retrieve.py` has to be done through command line, the rest can be done
through the webapp. To start it

$ python publivore/serve.py

And access it at http://127.0.0.1:5000

Multiple keywords in the search fields have to be single words separated by a
comma. A timestamp 'date:YYYY-MM-DD' can also be provided.

The recommendation tab provides 5 articles randomly out of the top 50 suggested
by your reading history.
