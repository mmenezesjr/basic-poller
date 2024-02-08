"""Polls participants from a csv file at random, balancing times polled.

Typical Usage:
with Poller(args.filename) as poller:
   for participant in poller:
       ...
       poller.attempted()
       ...
       poller.stop()

Alternatively:
poller = Poller(args.filename)
poller.open()
poller.shuffle()
for participant in poller:
   ...
   poller.attempted()
   ...
   poller.stop()
poller.save()

CSV File format:
<Name>,<#polled>,<#correct>,<#attempted>,<#excused>
Person0,8,2,4,0
Person1,7,0,2,0
"""

import math
import random

class Participant:
   """Participant keeps record of polls and outcomes.

   Attributes:
       name: Of the Participant.
       polled: How many times a participant is called.
       correct: How many times a participant answers correctly.
       attempted: How many times a participant answers incorrectly.
       excused: How many times a participant has an excuse for not answering.
   """

   def __init__(self, name, polled, correct, attempted, excused):
       self.name = name
       self.polled = polled
       self.correct = correct
       self.attempted = attempted
       self.excused = excused

   def __str__(self):
       """String formatted for saving in a csv file."""
       return ",".join([self.name,
                        str(self.polled), str(self.correct), str(self.attempted), str(self.excused)])

class Poller:
   """Shuffles and updates participant records."""

   # pylint: disable-next=used-before-assignment
   def __init__(self, filename, opener=open):
       """
       Args:
           filename: Path to a csv file containing participants.
           opener: For testing only, overridable open dependency for file IO.
       """
       self._filename = filename
       self._index = -1
       self._last_polled = 0
       self._opener = opener
       self._participants = []
       self._stopped = False
       self._to_poll = []
       self._total_polled = 0

   def attempted(self):
       """Increments polled/attempted columns for the current Participant."""
       self._polled()
       self._to_poll[self._index].attempted += 1

   def correct(self):
       """Increments polled/correct columns for the current Participant."""
       self._polled()
       self._to_poll[self._index].correct += 1

   def current_participant(self):
       """Get the name of the current participant"""
       return self._to_poll[self._index].name

   def excused(self):
       """Increments polled/excused columns for the current Participant."""
       self._polled()
       self._to_poll[self._index].excused += 1

   def missing(self):
       """Increments only the polled column for the current Participant."""
       self._polled()

   def open(self):
       """Loads participants from the filename into the Poller."""
       for line in self._opener(self._filename):
           if line != "":
               try:
                   name, polled, correct, attempted, excused = line.split(",")
                   participant = Participant(
                       name=name,
                       polled=int(polled),
                       correct=int(correct),
                       attempted=int(attempted),
                       excused=int(excused))
               except ValueError:
                   print('"' + line + '"')
                   raise ValueError(
                       "%s: Line formatted incorrectly: %s" % (self._filename, line))
               # Simple list of participants.
               # Maintains original order from loaded file.
               self._participants.append(participant)
       if len(self._participants) == 0:
           raise ValueError(
               "File %s does not contain participants" % self._filename)
       self._to_poll = self._participants[:]

   def save(self):
       """Writes participants in Poller back to filename."""
       with self._opener(self._filename, 'w') as f:
           for p in self._participants:
               f.write("%s\n" % str(p))

   def shuffle(self):
       """Shuffles the participants, keeping less polled at the front."""
       random.shuffle(self._to_poll)
       # sort is stable. This will bring the students who were polled less
       # to the front of the list.
       self._to_poll.sort(key=lambda x: x.polled)
       self._last_polled = self._to_poll[0].polled

   def stop(self):
       """Stops the next iteration of Poller."""
       self._stopped = True

   def total(self):
       """Returns the total polled participants since Poller created."""
       return self._total_polled

   def _polled(self):
       self._to_poll[self._index].polled += 1
       self._total_polled += 1

   def __iter__(self):
       self.shuffle()
       self._index = -1
       self._stopped = False
       return self

   def __enter__(self):
       """Equivalent to open()."""
       self.open()
       return self

   def __exit__(self, exc_type, exc_value, exc_traceback):
       """Equivalent to save()."""
       if exc_type is None:
           self.save()

   def __next__(self):
       """Iterates until stop() called.
      
       If the times polled among participants is unequal, this will re-shuffle
       the list to bring the less polled participants to the front.
       """
       if self._stopped:
           raise StopIteration()
       self._index += 1
       # If we're at the end or if participants need to be polled again to be
       # within 1 of their peers.
       if (self._index >= len(self._to_poll)) or (
               self._to_poll[self._index].polled > self._last_polled):
           self.shuffle()
           self._index = 0
       return self.current_participant()
