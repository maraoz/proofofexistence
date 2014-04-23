#! /usr/bin/python

import urllib2
from time import sleep

fin = open('in.txt', 'r')
for line in fin:
  q = line.strip()
  ret = urllib2.urlopen('http://proofofexistence.com/api/'+
    '2112fa301bab5e6e20b9b00c/bootstrap'+q)
  print ret.read()
  sleep(1)

  
