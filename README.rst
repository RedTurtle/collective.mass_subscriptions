Introduction
============

Subscribe a set of users taking from a CSV file all required data.

Details
-------

With this product you can import in your Plone site a full set of users, providing a CSV
file with all required and optional data. If your user's fieldset is customized you can also
provide non-standards ones.

The only required column is *username*. The *password* data, if not provided, will be
generated randomly.

You can send a notification message to those users, customizing the message text
(for example: to give to users the account's email address).

Add users to groups
-------------------

If you have powers to manage groups, you can also add all new users to one or more groups
available.

If you add a row named 'group' in the csv, the user will be added to that group.

For example::

    email,username,fullname,group
    jim@email.com,jim,Jim My,TeamA

Will add 'jim' to 'TeamA' group

Authors
=======

This product was developed by RedTurtle Technology team.

.. image:: http://www.redturtle.it/redturtle_banner.png
   :alt: RedTurtle Technology Site
   :target: http://www.redturtle.it/
