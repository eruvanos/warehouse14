# Warehouse14 Developer logbook

## 2021-07-12

While visiting the dynamodb backend to put in pagination, we discovered that 
also the storage `list` method would be limited to 3000 objects.
Because we never use the list on the storage, we removed it from the whole interface.


## 2021-07-04
Still problems with the basic Dynamodb backend implementation, reducing the amount of required methods to implement for a backend feels good. 

Following that path, we would provide
* account_save (nested tokens)
* account_get
* resolve_token

Account and project do have a nested object structure, account -> tokens and project -> member, admin, versions.
In case of a dynamodb, the often recommended representation of flat objects would result in an account be split up into multiple objects branching out the nested ones. To save an account, we would then have to sync the nested objects, remove not present ones from db, creating the new ones in db.
I am not sure about the consequences, if nested objects should be prevented in general. For account the methods to implement raise to:
* account_save (name, meta data)
* account_get
* resolve_token
* account_token_add
* account_token_list
* account_token_delete

Which should be easier to implement but are more work for new backends.

For now I will do A-B testing: accounts are flat objects and will be managed by specific repo interactions. Projects are managed as nested objects. 

🤷‍ let's see what works better

> Update: Saving project via `project_save` and resolve nested objects works 
> out okish, but was to much for version & files. 
> To reduce work I just saved versions
> as a nested object within the project entry. Looks fine so far.

