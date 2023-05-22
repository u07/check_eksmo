@echo off
set params=-af astats=metadata=1:reset=10000,ametadata=print:key=lavfi.astats.Overall.RMS_level:file="C:\Users\‹¥­¨­\Desktop\—¥ª § ¯¨á¥© ¤«ï ªá¬®\1.txt" -f null -
set params=-af astats,silencedetect=n=-45dB:d=1
::set params=-af astats=metadata=1:reset=1000,ametadata=print:file=- -f null -
::set params=-filter_complex ebur128
::set params= -filter_complex loudnorm=print_format=summary
::set params=-af astats=metadata=1:reset=10000000,ametadata=print:file=- -f null -
set file="C:\Users\‹¥­¨­\Desktop\—¥ª § ¯¨á¥© ¤«ï ªá¬®\Sample\022.mp3"

ffmpeg -hide_banner -nostats -loglevel info -i %file% %params% -vn -f null - 2>&1

pause