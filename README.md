# catalog-app
The fourth project into the Udacity's Full Stack Developer Nanodegree.  
This isn't a commercial project and has only academic purposes.

# About
This is an web application that provides a list of items within a variety of categories as well as provides an user authentication system.  Authenticated users will have the ability to post, edit and delete their own items.

The solution was written using **Python** and **SQLite**. The **Material Design Lite** component library was used to develop graphical interface.  
It explores some concepts about:
- Connections between an application and a database server
- Use of imports and native modules of Python
- Implementation of RESTful architecture
- JSON endpoints that provides the same data as the HTML endpoints.
- UI elements provided by **MDL** and UX improved.
- Developing with frameworks: [Flask](http://flask.pocoo.org/)
- Using an ORM: [SQLAlchemy](https://www.sqlalchemy.org/)
- Authentication and authorization
- Implementation of [OAuth2 using Google APIs in Python](https://developers.google.com/api-client-library/python/auth/web-app)
- Exception and error handling with custom views and messages  
(with app running, try visiting these endpoints: /not_allowed or /something_bad)

* To illustrate some error handling, some funcionalities were defined as:
  - When editing an item, an user can see the button and submit the form about editing operation. But if the user is not the item owner then will be redirected to a "not allowed" page and receives a message telling what happened.
  - When deleting an item, the same as described above gonna happen.  
Sneaky operations like log off and go back to the previous page won't be supported since the user is not authenticated, redirecting the user to the appropriated page.
  - Sneaky operations like log off and go back to the previous page won't be supported since the user is not authenticated, redirecting the user to the appropriated page.

# Requirements
The project will run inside a virtual machine provided by [VirtualBox](https://www.virtualbox.org/) and managed by [Vagrant](https://www.vagrantup.com/)

The ```Vagrantfile``` will be used to set the VM configuration. \
With the VM built with this file and running up, we are ready to go. 

The [Python](https://www.python.org/) language can be used with versions 2 and 3.  
The [SQLite](https://www.sqlite.org/index.html) database comes natively with Python since its version 2.5.  
The [Material Design Lite](https://getmdl.io) component library its used in v2.

obs: A `catalogapp.db` file will hold the entire data from the application.

# Running the project
1- Clone the repo to a folder on your local machine: \
```git clone https://github.com/reismatheus97/catalog-app.git```  

2- Get into the project folder: \
```cd catalog_app```  

3- Configure the virtual machine: \
```vagrant up```  

4- Connect to the virtual machine: \
```vagrant ssh```

5- Inside the VM SSH connection created, go to:  \
```cd / & cd /vagrant/catalog```

6- Run database setup: \
```python database_setup.py```

7- Run database setup: \
```python project.py```  

# JSON endpoints
The following endpoints supports data in JSON format:
  - /catalog_app/JSON - provides data about the entire catalog with all its categories and respectively items
  - /category/<int:category_id>/JSON - provides data about a specific category with its associated items.
  - /category/<int:category_id>/item/<int:item_id>/JSON - provides data about a specific item.




