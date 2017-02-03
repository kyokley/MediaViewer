from mediaviewer.models.person import Person

class Actor(Person):
    class Meta:
        app_label = 'mediaviewer'
        db_table = 'actor'
