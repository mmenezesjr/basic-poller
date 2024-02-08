import pytest
from poller import Participant, Poller
from collections import defaultdict

def mock_open(mock_text):

   class Opener:
       text = mock_text
       to_write = []
       iter_called = False

       def __init__(self, file_name, mode=""):
           pass

       def __iter__(self):
           Opener.iter_called = True
           if Opener.text == "":
               return iter([])
           return iter(Opener.text.split("\n"))
      
       def __enter__(self):
           return self

       def write(self, text):
           Opener.to_write.append(text)

       def __exit__(self, exc_type, exc_value, exc_traceback):
           if exc_type is None:
               if Opener.to_write:
                   Opener.text = "".join(Opener.to_write)
   return Opener

@pytest.fixture
def mock_0():
   return mock_open(
   "Person0,0,0,0,0\n"
   "Person1,0,0,0,0\n"
   )

@pytest.fixture
def mock_1():
   return mock_open(
   "Person0,0,0,0,0\n"
   )

def test_enter(mock_0):
   with Poller("test", mock_0):
       assert mock_0.iter_called

def test_exit(mock_1):
   with Poller("test", mock_1):
       pass
   assert mock_1.to_write == ["Person0,0,0,0,0\n"]

def test_attempted(mock_0):
   participants = set()
   with Poller("test", mock_0) as poller:
       for participant in poller:
           participants.add(participant)
           if len(participants) == 2:
               poller.stop()
           poller.attempted()
   assert mock_0.text == "Person0,1,0,1,0\nPerson1,1,0,1,0\n"
