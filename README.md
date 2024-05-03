# SWAPI clone

### What's this?

A basic fully-working REST api based on the Starwars API (SWAPI), made as an assignment for **4Geeks Academy Full-Stack** Bootcamp

It includes:
>- Useful and informative index page
>- **User**, **EntityType**, **Entity** and **Bookmark** tables
>- **Login** feature using a very basic *token* system (only usable through **Postman** or similar)
>- Database defaults in **JSON** format
>- Easy-to-define custom Entity and EntityTypes
>- **GET**, **POST** and **DELETE** endpoints to manage the database
>- **DEV** tools to create randomized rows, delete a random one, or **clear**/**reset** the database
>- Extra endpoints to use the **DEV** tools remotelly
>- Custom Command+Script to remake the entire DB with your models in < 10s *(in case everything fails)*

---

## Playing with the API

I recommend using **Postman** to test, as I did exported the **Postman** collection I created to to test it, it's on the repo root, with it you can login/logout and manage all the database

- **NOTE**: in **Postman**, you may need to set the **ENV** variable for **{{host}}**

---
### Check the API live

>1. Open this repo in **Github Codespaces**
>2. Run **`pipenv run upgrade`** to setup the database
>3. Run **`pipenv run start`** to start the **API** server
>4. Open the server page to test and/or play with the database
>5. Use the **Postman** collection provided to make better interactions

---
### Endpoints info:

    Method  Route                     Token?  Body?   Intended use
    -------------------------------------------------------------------------------------------------
    POST    /login                    no      yes     Obtain a session Token  
    POST    /logout                   yes     no      End a login session
    GET     /me                       yes     no      Get User <TOKEN>

    POST    /api/user                 no      yes     Create a User
    DELETE  /api/user                 yes     no      Delete the User <TOKEN>
    GET     /api/user/<name>          no      no      Get the User <name> info
    
    POST    /api/bookmark             yes     yes     Toggle a Bookmark for User <TOKEN>
    DELETE  /api/bookmark             yes     no      Delete all Bookmarks for User <TOKEN>
    GET     /api/bookmark             yes     no      Get all Bookmarks for User <TOKEN>
    POST    /api/bookmark?id          yes     no      Create Bookmark to Entity<id> for User <TOKEN>
    DELETE  /api/bookmark?id          yes     no      Delete Bookmark to Entity<id> for User <TOKEN>
    GET     /api/bookmark?id          yes     no      Check Bookmark to Entity<id> for User <TOKEN>

    POST    /api/entitytype           no      yes     Create an EntityType
    DELETE  /api/entitytype?id        no      no      Delete an EntityType<id>
    GET     /api/entitytype           no      no      Get all EntityTypes

    POST    /api/entity               no      yes     Create an Entity
    DELETE  /api/entity?id            no      no      Delete an Entity
    GET     /api/entity               no      no      Get all Entities
    GET     /api/entity/<type>        no      no      Get all Entities of type<type>
    GET     /api/entity/<type>/<id>   no      no      Get Entity with type<type> and id<id> info

    GET     /dev/user                 no      no      Get all Users
    GET     /dev/bookmark             no      no      Get all Bookmarks
    GET     /dev/test                 no      no      DEV tests
    GET     /execute?tool             no      no      Execute DEV tools

---
### Extra info:

  * You can only register **Entities** of existent **EntityTypes**
  * You cannot remove a **EntityType** if there's any **Entity** referencing it

---
### Database defaults

* By default this imitates **SWAPI**, so there are 5 **Users**, 6 **EntityTypes**, and 12 **Entities** *(2 of each)*
* **EntityTypes** are same as in **SWAPI**: *(but more can freely be added)*

      GET     /api/entity/films
      GET     /api/entity/people
      GET     /api/entity/planets
      GET     /api/entity/species
      GET     /api/entity/starships
      GET     /api/entity/vehicles

---
### Migrate broke my DB, what do i do?
We all know flask's `migrate` can do weird things, in that case just run **`pipenv run remake`** to automatically delete and re-create the entire DB *(rows will not survive)*

---
### Contributors

* Sergio 'sopze'
* Made from a basic template built by the 4Geeks Academy [Coding Bootcamp](https://4geeksacademy.com/us/coding-bootcamp)
