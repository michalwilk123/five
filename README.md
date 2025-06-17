

# initializes .five directory
```
five init
```

# build the index for each of objects in the project
```
five index
```

# example of usage of five shell
```
five shell
A: Hello what you want to do today?
U: Create me an endpoint that when called, returns me PDF version of receipts. Return me encoded base64 version of file
A: OK, looking for context # sends to the chatgpt command to generate the query from the above, then the query is used to find related objects
Found:
1) django model -> YES
... Piece of Recipe model ...
2) django serializer -> NO, but found context:
... some code used for context ...
3) django documentation tag -> YES
... 
4) django viewset -> NO, but found reference
... some code used for context ...
5) django route path -> NO, but found context:
...
6) django API Test case -> NO, but found context:
A: Do you want to add some extra context within project? If yes, then what is it? If no write no
U: Existing django view that generates the pdf recipe for the app users
A: Ok write me location of the code and the objects for which it is a context
U: apiv2/erecipe/viewsets.py 156:185 2,4 # first is path to file, second range of relevant code, third is the code object for which the context applies to
A: Do you want to add some extra context? If yes, then what is it? If no write no
U: Serializer which returns base64 output to external users # this may be irrelevant because of the search query, but adding example anyway
U: external_api/serializers/lab_results.py 24:36 2,4
A ... Optional: asking user about some other questions # generating questions based on query to chatgpt (asking what is missing)
A Summary:
Create me an endpoint that when called, returns me PDF version of receipts. Return me encoded base64 version of receipt file

Context:
1) django model
- django model found with initial search
- relevant django model found on initial search
2) django serializer
- django serializer found with initial search
- extra reference: Code to generate recipe (apiv2/erecipe/viewsets.py 156:185 1,3,4,5)
- django serializer found with initial search
3) django documentation tag
- extra reference: Code to generate recipe (apiv2/erecipe/viewsets.py 156:185 1,3,4,5)
4) django-viewset reference:
- reference found on initial search
- extra reference: Code to generate recipe (apiv2/erecipe/viewsets.py 156:185 1,3,4,5)
5) django-route-path
- django route tag found with initial search
6) django API Test case
- django-api-test found with initial search

Write `edit` if you want to change the summary in text editor, write `run` to start
U: run
A:
Generating the missing objects from top to bottom based on provided context. Click enter to continue, p for prompt, c to ignore changes and continue:
1) Django model: Using model Recipe from ...
U:
2) Django serializer: Generating serializer at location: external_api/serializers/recipe.py
... changes ...
U:
3) Django documentation tag: Generating documentation tag at location: external_api/drf_yasg_files/drf_yasg_constants/common.py
... changes ...
U:
4) Django viewset: Generating viewset at location: external_api/viewsets/recipe.py
... changes ...
U:
5) Django route path: Generating route path at location: external_api/urls/api_urls.py
... changes ...
U:
6) Django api test case: Generating serializer at location: external_api/serializers/recipe.py
... changes ...
U:
A: All done! You can now:
1) run the server and test the endpoint:

curl -X GET /api/v2/recipe/1/pdf/ -H "Authorization: Bearer <token>""

2) run the unit tests:
python manage.py test --settings=GabinetProject.config.settings_testing external_api.tests.test_views.TestRecipeViewSet

```

