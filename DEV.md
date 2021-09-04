# Warehouse14 Developer information

## Run local instance for testing

`run_local.py` starts local test setup with dynamodb and s3.
For login, a simple formfield is provided.

```bash
python run_local.py
```


## Commands

### Generate code highlighting
```
pygmentize -f html -S default>app/static/css/pygments.css
```

## Test strategy

### Test folder

* tests/
  * test_...  
    unit tests for repositories and components might use local service mocks like `dynamodb.jar`
    
  * enpoints/  
    use `requests_html` to test endpoints (mostly returning html)
    
  * integration/  
    use `pyppeteer` to test UI flow and main user interaction

### Where to test what?

* Code units that can be tested isolated (might use local system like dynamodb_local or file system)  
  -> `tests_...`

* Writing endpoints that change entries in the backend or database  
  -> `endpoints tests`

* Read endpoints that render data as html  
  -> `endpoints tests`
  
* Project creation flow  
  -> `integration`

* Infrastructure setup and health status of deployment  
  -> Not tested  
  (TODO provide script to check against a URL as smoke test)
  
## API specs

* [PEP 503 -- Simple Repository API](https://www.python.org/dev/peps/pep-0503/)
* [PEP 508 -- Dependency specification for Python Software Packages](https://www.python.org/dev/peps/pep-0508/)
* [Upload API](https://warehouse.pypa.io/api-reference/legacy.html#upload-api)
* [PEP 427 -- The Wheel Binary Package Format 1.0](https://www.python.org/dev/peps/pep-0427/#file-name-convention)
* [PEP 423 -- Naming conventions and recipes related to packaging](https://www.python.org/dev/peps/pep-0423/)
* [PEP 517 -- A build-system independent format for source trees](https://www.python.org/dev/peps/pep-0517/)
* [PEP 241 -- Metadata for Python Software Packages](https://www.python.org/dev/peps/pep-0241/)
* [PEP 314 -- Metadata for Python Software Packages 1.1](https://www.python.org/dev/peps/pep-0314/)
* [PEP 345 -- Metadata for Python Software Packages 1.2](https://www.python.org/dev/peps/pep-0345/)
* [PEP 426 -- Metadata for Python Software Packages 2.0](https://www.python.org/dev/peps/pep-0426/)
* [PEP 566 -- Metadata for Python Software Packages 2.1](https://www.python.org/dev/peps/pep-0566/)

### Package names
The current Python packaging landscape is full of historical grown specifications (PEP) and implementation details
of the former PyPI (Cheese shop). In the following sections some design decisions will be explained.

The allowed characters for a package name are defined in [PEP 508](https://www.python.org/dev/peps/pep-0508/#names)
which are ....
The simple API normalizes package following [PEP 503](https://www.python.org/dev/peps/pep-0503/#normalized-names) `re.sub(r"[-_.]+", "-", name).lower()`

For that reason `example-pkg`, `example.pkg`, `example+pkg` and `pkg_example` are the same. 

## Implementation details


### Security

#### Which library is used?
Authlib is used. While the project is still in beta (2021-06-01) it is referenced by OAuthlib as the recommended library.

#### Benefits against flask-oidc
Active development, dependencies are not deprecated.

#### Things to double-check
The implementation of the OAuth flow is created following the basic examples from Authlib.
Still, they do not include any information about how to implement a `requires_login` decorator beside a reference to Flask docs.

To not touch the Authlib state implementation the original destination is stored within the `session` and redirected to after.
The `next` url is not validated (Like recommended in Flask-Login), because it is stored in the `session`.

[Validate next url snippet](https://web.archive.org/web/20190128010142/http://flask.pocoo.org/snippets/62/)



### DynamoDB Schema
```markdown
# PK                             SK (GSI)                        TK      ATTRS

# store project and project permissions
project#project1                 project#project1                       {name: str, versions: Dict(str, Version)}   isarchived=True
project#project1                 account#account1                       {role: admin}
project#project1                 account#account2                       {role: member}
project#project1                 account#public                         {role: member}
                                                                                     
project#project2                 account#account1                       {role: admin}

# Group                                                                           
project#project1                 group#group1                           {role: member}
group#group1                     account#account1                       {role: admin}
group#group1                     account#account2                       {role: member}
// Permission per account for project
project#project1#group#group1    account#account1                       {role: member}

# store accounts and tokens
account#account1                 account#account1                        {...}
account#account1                 token#token1                            {...}
account#account1                 token#token2                            {...}

# project versions?
project#project1                 version#0.0.1#                          {role: member}

# Glocbal Secondary Index:
_: pk -> sk
sk_gis: sk -> pk
```

#### Project Query
```
query(sk=account#account1 & begins_with(PK, project#)) 
& 
query(sk=account#publicacc & begins_with(PK, project#))
```

#### Group Queries
- **get group projects**: `query[sk_gis](sk=group_key & pk startswith 'project#')`
- **get group members**: `query[pk_gis](pk=group_key & sk startswith 'account#')`

#### Group Actions
- Add    Member to Group: 
  **get group projects**, write item for each project
- Remove Member from Group
  **get group projects**, delete item for each project
- Add group to project:
  **get group members**, write item for each member
- Remove project:
  **get group members**, delete item for each member
- Change Group Permission for a project:
  **get group members**, update item for each member
```

