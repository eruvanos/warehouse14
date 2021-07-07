# Warehouse14 Developer information

## Commands

### Generate code highlighting
```
pygmentize -f html -S default>app/static/css/pygments.css
```

## API specs

* [PEP 503 -- Simple Repository API](https://www.python.org/dev/peps/pep-0503/)
* [Upload](https://warehouse.pypa.io/api-reference/legacy.html#upload-api)
* [PEP 241 -- Metadata for Python Software Packages](https://www.python.org/dev/peps/pep-0241/)
* [PEP 314 -- Metadata for Python Software Packages 1.1](https://www.python.org/dev/peps/pep-0314/)
* [PEP 345 -- Metadata for Python Software Packages 1.2](https://www.python.org/dev/peps/pep-0345/)
* [PEP 426 -- Metadata for Python Software Packages 2.0](https://www.python.org/dev/peps/pep-0426/)
* [PEP 566 -- Metadata for Python Software Packages 2.1](https://www.python.org/dev/peps/pep-0566/)



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
all_projects: 
    query(sk: account#account1 & begins_with(PK, project#)) 
    & 
    query(sk: account#publicacc & begins_with(PK, project#))

# PK                SK (GSI)

# store project and project permissions
project#project1    project#project1       {name: str, versions: Dict(str, Version)}
project#project1    account#account1       {role: admin}
project#project1    account#account2       {role: member}
project#project1    account#public         {role: member}

# project versions?
project#project1    version#0.0.1#         {role: member}

# store accounts and tokens
account#account1    account#account1
account#account1    token#token1
account#account1    token#token2
```

