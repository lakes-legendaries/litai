#########################
Contributing to this Repo
#########################

If you will be contributing to this repo, please adhere to all the standards
described on this page.

Pull requests are welcome.

*********
Standards
*********

#. All code should be error-free via :code:`flake8` linting.

#. Where applicable, use :code:`pytest`-compliant unit tests.

#. All code should be thoroughly tested before being checked in.

***************************
Continuous Integration (CI)
***************************

NEVER merge into the :code:`main` branch. Instead, merge into the
:code:`actions` branch, and the following will be automatically performed:

#. The code will be tested, and will NOT be merged into :code:`main` if
   there are any errors.

#. Documentation will be built and published to the :code:`docs` branch
   (which keeps the :code:`main` branch light).

   (To test documentation ahead of time, run :code:`docsrc/build`. NEVER
   check in documentation to your branch.)

#. The version number will be updated, and the repo will be
   tagged with the version number.

#. All changes will be merged into :code:`main`.
