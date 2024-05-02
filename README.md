# SWAPI clone

## What's this?

A basic fully-working REST api based on the Starwars API (SWAPI), made as an assignment for **4Geeks Academy Full-Stack** Bootcamp

It includes:
>- Useful and informative index page
>- **User**, **EntityType**, **Entity** and **Bookmark** tables
>- **Login** feature using a very basic *token* system
>- Database defaults in **JSON** format
>- Easy-to-define custom Entity and EntityTypes
>- **GET**, **POST**, **PUT** and **DELETE** endpoints to manage the database
>- Internal testing tools to create randomized rows or delete a random one
>- Additional endpoints to **reset**, **print** or **wipe** the database *(use with caution)*
>- Script to remake the entire DB with your models in < 10s *(in case everything fails)*

## Check the API live
>1. Open this repo in **Github Codespaces**
>2. Run **`pipenv run upgrade`** to setup the database
>3. Run **`pipenv run start`** to start the API server in port 3000
>4. Navigate to the port to test and/or interact with the database

## Migrate broke my DB, what do i do?
We all know flask's `migrate` can do weird things, in that case just run **`pipenv run remake`** to automatically delete and re-create the entire DB *(rows will not survive)*

### Contributors

This was made from a template built by the 4Geeks Academy [Coding Bootcamp](https://4geeksacademy.com/us/coding-bootcamp)
