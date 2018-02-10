=======
mychevy
=======


.. image:: https://img.shields.io/pypi/v/mychevy.svg
        :target: https://pypi.python.org/pypi/mychevy

.. image:: https://img.shields.io/travis/sdague/mychevy.svg
        :target: https://travis-ci.org/sdague/mychevy

.. image:: https://readthedocs.org/projects/mychevy/badge/?version=latest
        :target: https://mychevy.readthedocs.io/en/latest/?badge=latest
        :alt: Documentation Status

.. image:: https://pyup.io/repos/github/sdague/mychevy/shield.svg
     :target: https://pyup.io/repos/github/sdague/mychevy/
     :alt: Updates


Python interface to My Chevy website via Selenium

Unlike Tesla, GM does not provide a consumer level API to their vehicles. I
tried to sign up for their developer program after purchasing my Chevy Bolt,
but so far it's all been black holed. They do provide a useful My Chevy
website, where you can log in with your OnStar credentials and see things like
how charged your battery is. This is all built with a javascript framework, and
the data loads off the OnStar network with a 60 - 120 second delay (OnStar is a
rather slow proprietary cellular network)

This library does the craziest thing possible: uses a headless chrome
browser to log into the mychevy website, captures the session cookies needed to
interact with backend json services, then calls them.

Installation
============

Installation for this library is more than just a pip install, because you must
**also** install Google Chrome, and the Chrome Webdriver from selenium.

1. Install Google Chrome (real Chrome, Chromium doesn't count)
2. Install Chrome Web driver, put it in /usr/local/bin

.. code-block:: bash

   CHROME_DRIVER_VERSION=`curl -sS chromedriver.storage.googleapis.com/LATEST_RELEASE`
   wget -N http://chromedriver.storage.googleapis.com/$CHROME_DRIVER_VERSION/chromedriver_linux64.zip -P /tmp
   unzip /tmp/chromedriver_linux64.zip -d /tmp
   sudo install -m 0755 -o root /tmp/chromedriver /usr/local/bin/chromedriver


3. pip install mychevy

The last part will pull in all selenium bindings.

Usage
=====

Usage is very basic.

.. code-block:: python

   from mychevy.mychevy import MyChevy

   page = MyChevy("<username>", "<password>")
   # This takes up to 2 minutes to return, be patient

   # build credentials, needs real selenium
   page.login()

   # gets a list of cars associated with your account
   page.get_cars()

   # update stats for all cars, and returns the list of cars. This will take
   # 60+ seconds per car
   cars = page.update_cars()
   
   # Optionally you can call update_cars() with a vin of your choice to only update that car.
   cars = page.update_cars('vin number')

   # Percent battery charge
   print(cars[0].percent)


Every invocation of ``login()`` creates a whole separate browser to avoid
credential timeouts.

It is not recommended that you run this very frequently. Something like once an
hour will give you basic data, and shouldn't overload anyone's systems.

Testing
=======

Because there are so many ways this can go wrong, a basic cli tool has been
provided.

.. code-block:: bash

   > mychevy -c config.ini
   Loading data, this takes up to 2 minutes...
   <EVCar vin="...", range=185 miles, bat=100%, plugged_in=True, mileage=903 miles, charging=Your battery is fully charged., charge_mode=Departure Based, eta=None, state="">

config.ini must include your user and password for the mychevy site in the
following format, 'vin' is optional:

.. code-block:: ini

   [default]
   user = my@email.address
   passwd = my@wes0mepa55w0rd
   vin = KL821337VIN283498207

The ``mychevy`` command also takes the ``-S`` flag which makes the selenium
controlled web browser non headless during it's execution. This can be useful
for eyeballing why things go wrong (there are so many ways this can go wrong).

Caveats
=======

There are so many caveats.... This software aspires to be the gloriously robust
bubble gum and duct tape of which it has heard makes the internet go round.

* JSON formats are guessed at

  The use of the sessions capture and transfer, and inspecting json returned
  still creates slightly different parameters than are used by the website. The
  set of keys and values are guessed at. It's all kind of fragile and
  heuristic.

* The MyChevy website OnStar link is not robust

  In the first month with the Bolt I've seen two multi hour outages of the
  mychevy website being able to connect to their OnStar backend gateway. One
  lasted a whole day. The OnStar link from the Android App worked fine during
  these windows of time. So it's not an OnStar failure, but it's a lack of
  robustness somewhere on the Web side, or the gateway dedicated for serving
  OnStar requests.

* It launches a whole web browser to get a single python object

  It's cool that it all works, but it's a lot of moving parts.

As such, this software will always be classified Alpha on Pypi. It can and will
break. For that I'm sorry. But it's the best I've got.


* Free software: Apache Software License 2.0
* Documentation: https://mychevy.readthedocs.io.


Features
--------

* TODO

Credits
---------

This package was created with Cookiecutter_ and the `audreyr/cookiecutter-pypackage`_ project template.

.. _Cookiecutter: https://github.com/audreyr/cookiecutter
.. _`audreyr/cookiecutter-pypackage`: https://github.com/audreyr/cookiecutter-pypackage
