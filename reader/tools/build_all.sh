#!/bin/bash
set -e
cd /home/claude/work
python3 /home/claude/scripts/res_build.py
python3 /home/claude/scripts/pascha_build.py | tail -1
python3 /home/claude/scripts/deacon_build.py > /dev/null
python3 /home/claude/scripts/agpeya_build.py > /dev/null
python3 /home/claude/scripts/agpeya_final.py > /dev/null
D=/home/claude/app/data
python3 /home/claude/scripts/chunk_rows.py $D/pascha/*.json $D/agpeya.json $D/deacon.json | grep -v index || true
python3 /home/claude/scripts/build_library.py > /dev/null
python3 /home/claude/scripts/build_library2.py
python3 /home/claude/scripts/build_scripture.py | cut -c1-40
python3 /home/claude/scripts/build_library3.py
