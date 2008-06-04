from google.appengine.ext import bulkload
from google.appengine.api import datastore_types
from google.appengine.ext import search

class PersonLoader(bulkload.Loader):
  def __init__(self):
    # Our 'Person' entity contains a name string and an email
    bulkload.Loader.__init__(self, 'Person',
                         [('name', str),
                          ('email', datastore_types.Email),
                          ])

  def HandleEntity(self, entity):
    ent = search.SearchableEntity(entity)
    return ent

if __name__ == '__main__':
  bulkload.main(PersonLoader())
