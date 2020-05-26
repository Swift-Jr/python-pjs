#!/bin/bash

HOST=$1
DB_USER=$2

while ! pg_isready -h $HOST -p 5432 -U $DB_USER; do
    sleep 0.1 # wait for 1/10 of the second before check again
    echo 'Waiting for database..'
done

psql -h $HOST -U $DB_USER -c 'CREATE DATABASE pjs;'
