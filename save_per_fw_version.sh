#! /bin/bash

PRX_FOLDERS=("kd" "vsh/module")
FW_VERSIONS=("1.00" "1.03" "1.50" "1.51" "1.52" "2.00" "2.01" "2.50" "2.60" "2.70" "2.71" "2.80" "2.81" "2.82" "3.00" "3.01" "3.02" "3.03" "3.10" "3.11" "3.30" "3.40" "3.50" "3.51" "3.52" "3.60" "3.70" "3.71" "3.72" "3.73" "3.80" "3.90" "3.93" "3.95" "3.96" "4.00" "4.01" "4.05" "4.20" "4.21" "5.00" "5.01" "5.02" "5.03" "5.05" "5.50" "5.51" "5.55" "5.70" "6.00" "6.10" "6.20" "6.30" "6.31" "6.35" "6.36" "6.37" "6.38" "6.39" "6.60" "6.61" "vita-0.931" "vita-0.940" "vita-0.945" "vita-0.990" "vita-0.995" "vita-0.996" "vita-1.03" "vita-1.04" "vita-1.05" "vita-1.06" "vita-1.50" "vita-1.51" "vita-1.52" "vita-1.60" "vita-1.61" "vita-1.65" "vita-1.66" "vita-1.67" "vita-1.69.0" "vita-1.69.1" "vita-1.69.2" "vita-1.80" "vita-1.81" "vita-2.00" "vita-2.01" "vita-2.02" "vita-2.05" "vita-2.06" "vita-2.10" "vita-2.11" "vita-2.12" "vita-2.50" "vita-2.60" "vita-2.61" "vita-3.00" "vita-3.01" "vita-3.10" "vita-3.12" "vita-3.15" "vita-3.18" "vita-3.30" "vita-3.35" "vita-3.36" "vita-3.50" "vita-3.51" "vita-3.52" "vita-3.55" "vita-3.57" "vita-3.60" "vita-3.61" "vita-3.63" "vita-3.65" "vita-3.67" "vita-3.68" "vita-3.69" "vita-3.70" "vita-3.71" "vita-3.72" "vita-3.73")

PRX_FILES=()
for PRX_FOLDER in ${PRX_FOLDERS[@]}
do
    PRX_PATH="./PSPLibDoc/${PRX_FOLDER}/"
    if [ -d "${PRX_PATH}" ]; then
        mapfile -t -O "${#PRX_FILES[@]}" PRX_FILES < <(ls -1 "${PRX_PATH}"*.xml)
    fi
done

for fw in ${FW_VERSIONS[@]}; do
    COMBINED_LIBDOC_FILE="PSPLibDoc-$fw.xml"
    echo "Saving combined PSP-Libdoc file ${COMBINED_LIBDOC_FILE}"
    ./psp_libdoc.py -l ${PRX_FILES[@]} -v $fw -c "./PSPLibDoc/ByVersion/${COMBINED_LIBDOC_FILE}"
done

