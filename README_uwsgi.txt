uWSGI/Flask/nginx config followed from:

https://www.digitalocean.com/community/tutorials/how-to-serve-flask-applications-with-uswgi-and-nginx-on-ubuntu-18-04

to run the application with uWSGI:

$ conda activate wsgi
$ uwsgi --ini wsgi.ini
