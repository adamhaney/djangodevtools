Django Developer Tools
=======================

`djangodevtools` is a collection of code quality and convenience tools for developers who are creating Django applications.

Helpful Tools
-------------

We can separate the commands into subject areas

Quality and Documentation
^^^^^^^^^^^^^^^^^^^^^^^^^

cc --> cyclomatic complexity computing
epydocs --> API documentation for all Python modules
flakes --> this command runs pyflakes syntax checks
pep8 --> having consistent style throughout the code helps to keep the quality in terms of simplicity, understanding and all their benefits

Testing
^^^^^^^

cover --> in addition of Ned's tools our command allows the coverage computation not only on application tests but on every command
itest --> command to run Wsgi tests
selenium --> Selenium integration tests
test_env --> zap the database and load the fixtures

Javascript optimization
^^^^^^^^^^^^^^^^^^^^^^^
closure --> the result is optimized, lightweight and maintainable code, based on Google Javascript Style Guide
jsmin --> it edits Javascript code deleting the characters which are insignificant, removing comments and most spaces and linefeeds. This function accepts only one js file as an input, if you put more files it will use the last one.

Utility
^^^^^^^
alias --> it saves commands and parameters as shortcuts
tocsv --> this feature exports models schema using csv encoding
xshell -->tThis command runs a shell interface for your project in which all models are loaded (so, you don't need to import them).

Database
^^^^^^^^
xloaddata --> it is a more verbosing loaddata,often, in developing, some changes may send wrong the fixtures. xloaddata tell you which is last good fixture loaded before the error (is just a print of obj)
xsyncdb --> it is just the syncdb taken from 1.3alpha. In 1.3 is possible use an hidden load_initial_data parameter
zap --> it makes a flush of the database: all data in your db will be destroyed and the features returns a database to the state it was in after syncdb


More Information
----------------

More informationa and further documentation for this project can be found at:

  - http://www.os4d.org/djangodevtools
