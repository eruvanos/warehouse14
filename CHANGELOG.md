# Changelog
           

## 0.2.0

* bump pydantic from 1.8.2 to 1.10.7 
* bump requests from 2.26.0 to 2.29.0 
* bump pyppeteer from 0.2.6 to 1.0.2
* bump flask-login from 0.5.0 to 0.6.2
* bump flask-wtf from 0.15.1 to 1.1.1
* bump authlib from 0.15.4 to 1.2.0

## 0.1.13

* fix project not updated

## 0.1.12
- improve token information page
- improved information for wrong token login
- improved user flow

## 0.1.11
- improved setup (default to random session secret)
- allow only specific users to create new projects
- improved user management UI
- preparation for groups

## 0.1.10
- improve OIDC configuration code
- restrict user management 🥶

## 0.1.9
- improved token representation in code and pre blocks
- show no project text and be kind
- prevent adding empty users
- test remove and add admin/member endpoints
- use logger within endpoints
- add pagination for dynamodb query and scan
- remove `list` from Storage

## 0.1.8
- support multiple versions

## 0.1.7
- small improvements

## 0.1.6
- enforce binary mimetype for static file download

## 0.1.5
- save non normalized project name

## 0.1.4
- additional logging within simple_api

## 0.1.3
- small ui fixes

## 0.1.2
- add customer guidance
- fix project storage, use normalized name as primary key
- replace leftovers from old names 

## 0.1.1
- implement `account_token_delete` for dynamodb
- fix adding users to project
