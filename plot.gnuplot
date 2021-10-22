set xrange [1:46]
set yrange [0:100]
plot "table.txt" using 3 with linespoints, "table.txt" using 4 with linespoints
