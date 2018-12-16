from django.db import connection
from django.test.runner import DiscoverRunner

class MVDiscoverRunner(DiscoverRunner):
    def setup_databases(self, **kwargs):
        config = super(MVDiscoverRunner, self).setup_databases(**kwargs)

        with open('setup.sql', 'r') as infile:
            sql_file = infile.readlines()

        sql_file = split_queries(sql_file)

        for query in sql_file:
            try:
                cursor = connection.cursor()
                cursor.execute(query);
            except Exception as e:
                print('Warning: %s Got exception running: %s' % (str(e), query))
        return config

def split_queries(sql_file):
    current_line = ''
    queries = []
    for line in sql_file:
        line = line.strip()
        if not line:
            continue

        if line.lower() == 'begin;':
            current_line = ''
        elif line.lower() == 'commit;':
            queries.append(current_line)
        else:
            current_line = '%s %s' % (current_line, line)
    return queries
