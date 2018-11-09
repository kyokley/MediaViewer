from mediaviewer.models.person import Person


class Writer(Person):
    class Meta:
        app_label = 'mediaviewer'
        db_table = 'writer'
