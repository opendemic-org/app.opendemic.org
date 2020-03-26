#!/usr/bin/env bash
git stash
git checkout master
git merge dev
git push -u origin master
git checkout dev
git stash pop