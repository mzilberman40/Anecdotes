import psycopg2
import datetime
from operator import attrgetter

TEXTTYPES = {'text', 'character', 'character varying'}
LOGICALTYPES = {'boolean'}
NUMTYPES = {'bigint', 'bigserial', 'bit', 'bit varying', 'integer', 'real', 'serial', 'smallint', 'smallserial'}

def _check_value(string):
    """
    If string consists quote, change it to 2 quotes.
    This is necessary for DB request shielding
    :param string:
    :return: corrected string
    """
    return string.replace("'", "''")

def dict2req(dic):
    """
    :param dic: dictionary
    :return: (list_of_keys, list_of_corresponding_values)
    """
    fields = list()
    values = list()
    for k in dic.keys():
        fields.append(k)
        values.append(_check_value(dic[k]))
    return fields, values

def rec2req(record):
    """
       :param dic: dictionary
       :return: (list_of_keys, list_of_corresponding_values)
       """
    fields = list()
    values = list()
    for k in record.keys():
        fields.append(k)
        values.append(_check_value(record[k]))
    return fields, values

class psgsqlException(Exception):
    pass

class Record(dict):
    """
    Describes possible record in the DB
    :param dicrionary is a dict where keys is the field, values is field's value

    def __init__(self, columns, values):
        self.columns = columns
        self.values = values
     """
    pass

class DBTableColumn:
    def __init__(self, _tuple):
        self.name = _tuple[0]
        self.position = _tuple[1]
        self.default = _tuple[2]
        self.is_nullable = _tuple[3]
        self.data_type = _tuple[4]
        self.constraint_name = _tuple[5]
        self.constraint_type = _tuple[6]
        self.ispkey = (self.constraint_type == 'PRIMARY KEY')

    def __repr__(self):
        return self.name

class OpenDB:
    """
    Context manager for open SB
    - 'host' - hostname o ip address of sql server
    - 'db' - DB name
    - 'user' - username
    - 'passwd' - md5 password string
    """

    def __init__(self, params):
        self.host = params['host']
        self.db_name = params['db']
        self.user = params['user']
        self.password = params['password']
        self.conn = self._connect()
        self.cursor = self.conn.cursor()

    def __enter__(self):
        return self.conn

    def _connect(self):
        """
        get a DB connection. An exception will be raised  if a connection cannot be made
        :return: instance of class connection.
        """
        conn_string = f"host={self.host} dbname={self.db_name} user={self.user} password={self.password}"
        print(f"Connecting to database\n	->{conn_string}")
        try:
            conn = psycopg2.connect(conn_string)
            print("Connected!\n")
            return conn
        except psycopg2.Error as err:
            print(f"Can't connect: {err.pgcode}: {err.pgerror}")
            exit()

    def __exit__(self, *args):
        self.conn.commit()
        self.conn.close()
        print("  Committed!  \n"
              " Disconnected!")

class SqlDB:
    def __init__(self, conn, params):
        self.conn = conn
        self.cursor = self.conn.cursor()

    def _whoami(self):
        req = "SELECT current_user"
        ans = self._try(req)
        return ans[0][0]

    def _try(self, request, to_commit=False):
        try:
            self.cursor.execute(request)
            ans = self.cursor.fetchall()
        except psycopg2.Error as er:
            print(er.pgcode, er.pgerror)
            ans = [[-1]]

        if to_commit and ans:
            self.conn.commit()
            print("Done. Commited")
            print(f"ans = {ans}")

        return ans

class SqlDBTable(SqlDB):
    """
    Class for objects stored in the specific table of the PostgresSQL DB
    - 'table' - tablename
    """

    def __init__(self, cursor, params):
        super().__init__(cursor, params)
        self.t_name = params['table_name']
        self.t_schema = params['table_schema']
        self.fields = self._fields()
        _p = [f.ispkey for f in self.fields]
        try:
            self.pkey = self.fields[_p.index(1)]
        except:
            self.pkey = None
            raise psgsqlException("Cannot work with tables without primary key!!!!")


    def __repr__(self):
        return f"DBTable: {self.t_name}, DBschema: {self.t_schema}"

    def _fields(self):
        """
            Returns sorted by position_number list of DBTableColumn - objects for this DBTable
        """

        req = f"""
        SELECT c.column_name, c.ordinal_position, c.column_default, c.is_nullable, c.data_type, ccu.constraint_name, 
        tc.constraint_type
        FROM information_schema.columns AS c
        FULL JOIN information_schema.CONSTRAINT_COLUMN_USAGE AS ccu
        RIGHT JOIN information_schema.TABLE_CONSTRAINTS AS tc
        ON tc.constraint_name = ccu.constraint_name
        ON c.column_name = ccu.column_name
        WHERE c.table_schema='{self.t_schema}' AND c.table_name='{self.t_name}'
        """
        fields = [DBTableColumn(f) for f in self._try(req)]
        return sorted(fields, key=attrgetter('position'))

    def search_field(self, fname):
        for f in self.fields:
            if fname == f.name:
                return f
        return None

    def len(self):
        """
        :return: db length - number of records in the table or -1 in case of error
        """
        req = f"SELECT COUNT(*) FROM {self.t_name}"
        return self._try(req)[0][0]

    def getall(self):
        req = f"SELECT * FROM {self.t_name}"
        return [Record(zip([f.name for f in self.fields], rec)) for rec in self._try(req)]

    def iskey(self, key):
        """
        Check if key exists
        :param key:
        :return: boolean, True or False
        """
        req = f"SELECT COUNT({self.pkey}) FROM {self.t_name} WHERE {self.pkey}={key}"
        ans = self._try(req)
        return ans[0][0] > 0

    def delete(self, key):
        """
        Delete key-value pair from DB
        :param key:
        :return: deleted record
        """
        if not self.iskey(key):
            print("Wrong key!!!")
            return -1
        req = f"DELETE FROM {self.t_name} WHERE id={key} RETURNING *"
        return self._try(req, True)

    def keys(self, filter=None):
        """
        :param filter: list of tuples: (field, string)
        :return: list of all pkeys that matches the filter criteria
        """
        if filter:
            fi = list()
            # print(filter)
            for f in filter:
                field = self.search_field(f[0])
                # print(field.data_type)

                if field is not None:
                    if field.data_type in TEXTTYPES:        # search by substring is possible
                        fi.append(f"{f[0]} ILIKE '%{f[1]}%'")
                    elif field.data_type in NUMTYPES | LOGICALTYPES :  # search for exact match is possible
                        fi.append(f"{f[0]} = {f[1]}")
                    else:
                        continue

            req = f"SELECT {self.pkey} FROM {self.t_name} WHERE {'AND'.join(fi)} "
        else:
            req = f"SELECT {self.pkey} FROM {self.t_name}"

        return [r[0] for r in self._try(req)] if self.pkey else []


    def get(self, key, default=None):
        """
        Returns value for given key. If te key doesn't exist returns default, None by default
        :param key:
        :param default:
        :return:
        """
        if not self.iskey(key):
            return default
        req = f"SELECT * FROM {self.t_name} WHERE {self.pkey}={key}"
        ans = Record(zip([f.name for f in self.fields], self._try(req)[0]))
        # print(f"Pgsql, get, key={key}, ans={ans}")
        return ans

    def add(self, record):
        """
        Add given dict object to te DB
        :param dict object
        :return: key of new record
        """
        fields, values = rec2req(record)
        req = f"INSERT INTO {self.t_name} ({', '.join(fields)}) VALUES ('{', '.join(values)}') RETURNING {self.pkey}"
        return self._try(req, True)[0][0]

    def update(self, record):
        """
        Update record in the DB
        """
        rkey = record.get(str(self.pkey))  # primary key of updating record
        if self.iskey(rkey):
            toupdate = [f"{c}='{record[c]}'" for c in record.keys()]
            req = f"UPDATE  {self.t_name} SET {', '.join(toupdate)} WHERE {self.pkey}={rkey} RETURNING {self.pkey}"
            ans = self._try(req, True)[0][0]
        else:
            ans = -99

        return ans


if __name__ == "__main__":
    import config
    with OpenDB(config.db_params) as a:
        anecdotes = SqlDBTable(a, config.anecdot_params)
        print(anecdotes)
        print(f"DBUser: {anecdotes._whoami()}")
        print(f"Number of records in the DB: {anecdotes.len()}")
        #print(anecdotes.iskey(111))
        #print(anecdotes.fields)
        #print(anecdotes.keys([("anecdote", "еврей")]))
        #print(ans)
        #ans = anecdotes.getall()
        #print(ans)
        #print(type(anecdotes.pkey), anecdotes.pkey, anecdotes.pkey.name)

        #an1 = {'anecdote': "ХаПиздецаЭ"}
        #rec1 = Record(an1)
        #print(rec1)
        #print(anecdotes.add(rec1))
        #an2 = {'anecdote': "חילחילחילחילחיחיחי", 'id': 906}
        #rec2 = Record(an2)
        #print(rec2.keys())
        #print(rec2[anecdotes.pkey.name])
        #print(anecdotes.get(905))
        #print(anecdotes.update(rec2))
        #print(anecdotes.get(842))

        #print(anecdotes.delete(899))
        #print(anecdotes.keys())
        #print(anecdotes.keys([('id', 471)]))
        req = anecdotes.get(679)
        t = req['creationtime']
        print(t,  type(t), t.date())
        #print(datetime.datetime(t))
