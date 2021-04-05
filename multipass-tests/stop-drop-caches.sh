#!/bin/bash
set -e
source common
ExecEach -e bash -lc vula-stop-drop-caches
