from mediaviewer.models.person import Person

class Director(Person):
    class Meta:
        app_label = 'mediaviewer'
        db_table = 'director'
