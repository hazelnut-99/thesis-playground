awk -F, 'NR>1 {a[$3]++; if(min==""){min=max=$3}; if($3<min) min=$3; if($3>max) max=$3} END {for (i in a) sum+=i; print "Min:", min, "Max:", max, "Sum of unique values:", sum}' file.csv
