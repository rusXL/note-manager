Here is the example of how I would like to have mongodb database:

{
  "_id": "user1",
  "email": "john.doe@example.com",
  "name": "John Doe",
  "folders": [
  {
    "_id": "folder1",
    "name": "work",
    "color": "blue",
  }]
}

{
  "_id": "folder1",
  "name": "work",
  "color": "blue",
  "description": "Work-related tasks",
  "user_id": "user1",
  "notes": [
    {
      "_id": "note1",
      "name": "Setup project",
    },
    {
      "_id": "note2",
      "name": "Implementing Database",
    }
  ],
  "folders": [
  {
    "_id": "folder99",
    "name": "secret"
    "color": "pink"
  }
  ]
}

{
  "_id": "note2",
  "parent_folder": "folder1",
  "name": "Implementing Database",
  "content": "Implement the database based on the given description",
  "deadline": "2025-11-20",
  "priority": 2,
  "image": {
    "url": "https://example.com/image.jpg",
    "caption": "Implementing Database"
  }
}


Create a the init database script in database.py for mongodb.
Fill it with the same mock data as in data_init() method (currently it works for maria DB).

DO not remove SQL database code. Make new methods for mongodb database (when use_sql is set to False).
