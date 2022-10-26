# Rate Limit Example with LaunchDarkly
A Flask-based RESTful API which shows LD flag targeting & uses returned flag values. Redis is used as a data store.

## Install steps   
Assuming you have Python 3 installed. Testing with Python 3.10.5
1. Clone the repository
2. Install redis and enable service. 
3. In your LaunchDarkly project, create 2 flags
    * Flag key: `api-rate-limiter`. Type: Number. Purpose: 
    * Flag key: `api-write-permission`. Type: Boolean. Purpose: If true, allows request to create/modify/delete flavors.  
4. Run `pip -r requirements.txt`
5. Run `python index.py`

## Todo:
- [ ] Add logic to use returned rate limit as needed; currently rate limit reset for each request.
- [ ] Create a NodeJS version

## Functions available:
*Get all flavors:*   
`$ curl -v http://server_name/api/v1/flavors`

*Get a specific flavor:*  
`$ curl -v http://server_name/api/v1/flavors/FLAVOR_NAME`

*Create a new flavor:*  
`$ curl -v -H "Content-Type: application/json" -X POST -d
'{"name":FLAVOR_NAME, "stock":FLAVOR_AMOUNT}' -H 'Authorizationhttp://server_name/api/v1/flavors`

*Modify an existing flavor:*  
`$ curl -v -H "Content-Type: application/json" -X PUT -d
'{"name":NEW_FLAVOR_NAME, "stock":NEW_FLAVOR_AMOUNT}' http://server_name/api/v1/flavors/FLAVOR_NAME`

*Delete a flavor:*  
`$ curl -v -X DELETE http://server_name/api/v1/flavors/FLAVOR_NAME`

## Postman Collection
Including the Postman collection for API requests. Import file: **LD-API-Rate-Limiter.postman_collection**