#!/usr/bin/env bash
set -e

backup_script=$(realpath litres-backup.py)

[[ -d downloads ]] || mkdir downloads
cd downloads

for format in fb3 fb2.zip html.zip txt.zip rtf.zip a4.pdf a6.pdf mobi.prc epub ios.epub; do
    dir="${format/\./-}"
    echo "Syncing $dir..."

    [[ -d "$dir" ]] || mkdir "$dir"
    cd "$dir"
    "$backup_script" -f $format "$@"
    cd ..
done
