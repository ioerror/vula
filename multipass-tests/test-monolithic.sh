#!/bin/bash
source common
ExecEach sudo systemctl disable vula-organize
./stop-drop-caches.sh
ExecEach sudo systemctl start vula-organize-monolithic
./test.sh
