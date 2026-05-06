pgAdmin has been added to the compose file. Here's a summary of what was added:

Image: dpage/pgadmin4:latest
URL: http://localhost:5050
Login: admin@admin.com / admin
Depends on: the db service being healthy before starting
To connect to your Postgres instance from within pgAdmin, use these connection details:

Host: db
Port: 5432
Username: bale_bot
Password: dev_password
Database: bale_bot