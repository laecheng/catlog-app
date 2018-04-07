# Catlog Web Application
  - This is a web application developed in **Python** with **Flask** Framework. This website provide basic create, read, update, and delete
  functionality. 

# Environment
  - **Python** with version 2.7
  - Follow this [guidance](https://www.python.org/about/gettingstarted/) to install Python.
  - **Flask**
  - Follow this [guidance](http://flask.pocoo.org/docs/0.12/installation/) to install Flask.
  - **VirtualBox** and **Vagrant**
  - Install [VirtualBox](https://www.virtualbox.org/wiki/Downloads) and [Vagrant](https://www.vagrantup.com/downloads.html)
  - Downloads the Vagrant Config File [Here](https://d17h27t6h515a5.cloudfront.net/topher/2016/August/57b5f73b_vagrantfile/vagrantfile)
  
# How to Run
  - Install virtual box and vagrant. 
  - In your local machine where the vagrant config file located and run the following command
  ```
  $ vagrant up
  $ vagrant ssh
  $ cd /vagrant
  $ git clone git@github.com:laecheng/catlog-app.git .
  ```
  - You need to set up the database first, the application is based on SQLite. The SQLite should already been installed when you build your
  virtual machine with the vagrant config file
  ```
  $ python database_setup.py
  $ python data.py
  ```
  - Database is set and data is loaded into the database, now you can run this app on your virtual machine on port 5000
  ```
  $ python application.py
  ```
  - The application is now running, you can use the browser on your local machine to access the application on **http://localhost:5000/catlog**
