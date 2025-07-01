#!/usr/bin/python
# ---------------------------------------------------------------------------
#   Store.py - WRW 31-Jan-2025
#       This is an attempt at a global store for variables like conf and dc
#        instead of passing a bunch of variables around as with the PySimpleGui birdland.
#   Credit to ChatGPT, lots of credit, for ensuring this is a true Singleton
#       and for help with dot notation.
# ---------------------------------------------------------------------------

class Store:
    _instance = None  # Class-level attribute to hold the singleton instance

    def __new__(cls):
        if cls._instance is None:                   # Check if an instance already exists
            cls._instance = super().__new__(cls)    # Create a new instance
            cls._instance._data = DotDict()
        return cls._instance                        # Return the existing instance

    def setVal( self, name, val ):
        self._data[name] = self._convert_to_dotdict(val)

    def getVal( self, name ):
        if name in self._data:
            return self._data[name]
        raise AttributeError(f"'{self.__class__.__name__}' object has no attribute '{name}'")

    def __setattr__(self, name, value):
        if name != "_data":
            self._data[name] = self._convert_to_dotdict(value)
        else:
            super().__setattr__(name, value)

    def __getattr__(self, name):
        if name not in self._data:
            self._data[name] = DotDict()
        return self._data[name]

    def _convert_to_dotdict(self, value):
        if isinstance(value, dict):
            return DotDict(value)
        return value


    def defined( self, name ):
        return True if name in self._data else False

    def showKeys( self ):
        return list(self._data.keys())

    def showItems( self ):
         return [f"{key:>20} : {val}" for key, val in self._data.items()]

# ---------------------------------------------------------------------------
#   This allows accessing dictionary keys as attributes (dot notation)

class DotDict(dict):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for key, value in self.items():
            self[key] = self._convert_nested(value)

    def __getattr__(self, name):
        if name in self:
            value = self[name]
            self[name] = self._convert_nested(value)
            return self[name]
        self[name] = DotDict()
        return self[name]

    def __setattr__(self, name, value):
        self[name] = self._convert_nested(value)

    def _convert_nested(self, value):
        if isinstance(value, dict) and not isinstance(value, DotDict):
            return DotDict(value)
        return value

# ---------------------------------------------------------------------------

def do_main():
    import sys

    print( "Call Store class" )
    s = Store()
    print( f"{s=}" )
    t = Store()
    print( f"{t=}" )
    print( f"{s == t=}" )

    print()
    print( "Using setVal() / getVal()" )

    s.setVal( "dc", "this is a test of dc" )
    print( f"{s.getVal( "dc" )=}" )

    s.setVal( "db_params", {
            "host": "localhost",
            "port": 5432,
            "user": "admin",
            "password": "password",
            "nest" : { 'a' : "A item in nest", 'b' : "B item in nest" },
        } )

    print( f"{s.getVal( "db_params" )=}")

    print( f"{t.getVal( "dc" )=}")
    print( f"{t.getVal( "db_params" )=}" )

    t.setVal( "int", 1234 )
    print( f"{s.getVal( "int" )=}" )


    print( "Reference by attribute with dot notation:" )
    print( f"{s.dc=}" )
    print( f"{s.int=}" )
    print( f"{s.db_params=}" )
    print( f"{s.db_params.keys()=}" )
    print()

    print( "Reference nested by attribute with index notation:" )
    print( f"{s.db_params['port']=}", f"{s.db_params['user']=}" )
    print( f"{s.db_params.nest['a']=}", f"{s.db_params.nest['b']=}" )
    print()

    print( "Reference nested by attribute with dot notation:" )
    print( f"{s.db_params.port=}", f"{s.db_params.user=}" )
    print( f"{s.db_params.nest.a=}", f"{s.db_params.nest.b=}" )

    print()
    print( "Assigning with new attribute" )
    s.newvar = "This is a new var"
    print( f"{t.newvar=}" )

    print()
    print( "Using nested attributes" )

    s.newdict = { 'a' : 'a', 'b' : { 'a' : 'a', 'b' : { 'a' : 'a', 'b': 'b' }}}
    print( f"{s.newdict=}" )
    print( f"{s.newdict.a=}" )
    print( f"{s.newdict.b=}" )
    print( f"{s.newdict.b.a=}" )
    print( f"{s.newdict.b.b=}" )
    print( f"{s.newdict.b.b.a=}" )
    print( f"{s.newdict.b.b.b=}" )

    print()
    print( "Reference non-existent key with getVal()" )
    try:
        x = s.getVal( "xxx" )
    except Exception as e:
        (extype, value, traceback) = sys.exc_info()
        print( f"Exception: type: {extype}, value: {value}" )
    print()

    print( "Reference non-existent key with dot notation" )
    try:
        x = s.xxx   
    except Exception as e:
        (extype, value, traceback) = sys.exc_info()
        print( f"Exception: type: {extype}, value: {value}" )
    print()


    print( "Reference non-existent nested key with index notation" )
    try:
        x = s.newdict.b.b['xxx']
    except Exception as e:
        (extype, value, traceback) = sys.exc_info()
        print( f"Exception: type: {extype}, value: {value}" )
    print()

    print( "Reference non-existent nested key with dot notation" )
    try:
        x = s.newdict.b.b.xxx
    except Exception as e:
        (extype, value, traceback) = sys.exc_info()
        print( f"Exception: type: {extype}, value: {value}" )
    print()

    print( "Showing all stored variable names" )
    print(s.showKeys())

    print()
    print( "Showing all stored variables" )
    print(s.showItems())

    print( "Assigning nested variables" )

    s.ui = dict()
    print( s.ui )
    s.ui['e1'] = 1234
    print( f"{s.ui['e1']=}" )

    s.ui.e2 = 5678
    print( f"{s.ui.e2=}" )

    s.ux.a = 'nested assignment without initalization'
    print( f"{s.ux.a=}" )

# ---------------------------------------------------------------------------

if __name__ == "__main__":
    do_main()

# ---------------------------------------------------------------------------
