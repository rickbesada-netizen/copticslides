#!/bin/sh
# Rebuild the rite books. Usage: tools/build_all_rites.sh <folder with the PDFs>
set -e
A="$1"; O="$(dirname "$0")/../data"; T="$(dirname "$0")"
python3 "$T/build_rites.py" "$A/Rites_Baptism1.pdf" "$O/baptism.json" bap "Absolution of the Mother — Boy|5|تحليل المرأة إذا ولدت ذكراً" "Absolution of the Mother — Girl|34|تحليل المرأة إذا ولدت أنثى" "Order of the Holy Baptism|61|طقس المعمودية المقدسة" "Anointing with the Holy Myron|132|الرشم بالميرون المقدس"
python3 "$T/build_rites.py" "$A/lakan-of-epiphany1.pdf" "$O/laqan-epiphany.json" lqe "Laqan of the Epiphany|5|لقان عيد الظهور الإلهي" "The Anaphora of the Water and the Absolutions|76|قداس الماء والتحاليل" "Conclusion of the Laqan|88|ختام اللقان"
python3 "$T/build_rites.py" "$A/Rites_Laqan_Fast_Feast_Apostles1.pdf" "$O/apostles.json" apo "Fast of the Apostles|5|صوم الرسل" "Feast of the Apostles|23|عيد الرسل" "Laqan of the Apostles|42|لقان عيد الرسل"
python3 "$T/build_rites.py" "$A/Rites_Prostration_Sagda1.pdf" "$O/prostration.json" pro "Instructions|5|تعليمات" "The First Prostration|8|السجدة الأولى" "The Second Prostration|87|السجدة الثانية" "The Third Prostration|125|السجدة الثالثة"
python3 "$T/add_rites_library.py"
