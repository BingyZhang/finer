#!/bin/sh
# usage: bingmail.sh 'subject' 'body' 'recipient'
subject=$1
body=$2
recipient=$3

echo "From: no-reply@tal.di.uoa.gr
subject:$subject
$body
."  | sendmail -v $recipient
