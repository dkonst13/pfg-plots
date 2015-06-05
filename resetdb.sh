#!/bin/bash

rm -fv pfgplots.sqlite3
sqlite3 pfgplots.db ".read dbschema.sql"
