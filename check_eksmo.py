#
#    А. Петелин, 2023
#	 Обновлено 21.09.2023
#
#  Работает с облегчённым ffmpeg (в комплекте) либо с обычным 2023-04-17-git-65e537b833-essentials_build-www.gyan.dev win 64 2023 gcc 12.2.0
#  

def on_error(exc_type, exc_value, exc_traceback):
	import traceback
	traceback.print_exception(exc_type, exc_value, exc_traceback)
	input(f"\nТысяча чертей! Какая-то дурацкая ошибка! \n\n {exc_value}\n")
	sys.exit(-1)

print("\nЗагрузка...", end='\r')
import sys; sys.excepthook = on_error
import os
import re
import csv
import asyncio
import subprocess
import multiprocessing
import tempfile
import webbrowser
import datetime


help_string = """ Эта утилита проверит ваши аудиокниги на соответствие требованиям 
 издательства Эксмо. Принимаются файлы mp3, wav, flac и папки.
 
 Пример запуска: check_eksmo "D:\Книга 1\" "D:\Книга 2\" 
 
 Или просто перетащите файл/папку сюда и нажмите Enter: 

"""

MAX_CONCURRENT_TASKS = max(4, multiprocessing.cpu_count())

# Тут выполняем все возможные проверки
def parse_ffmpeg_output(text, shortname):
	try:
		result = ()
		good = "g"
		bad = "b"  
		compromise = "c" 
		neutral = "n"
		not_shit = lambda txt: txt and all(x not in txt for x in "óåûàîýÿèþÐ¾ÐÑ") # уеыаоэяию
		
		# 001.mp3 - 999.mp3 or Sample
		file_base, file_ext = os.path.splitext(shortname)
		val = shortname
		col = good if ((len(file_base) == 3) and (file_base.isdigit())) or (file_base.lower() == 'sample') else bad
		comm = "Файлы нумеруются трехзначными числами от 001"
		result += (('Файл', val, col, comm), )
		
		#Metadata:
		#	title           : sample
		match = re.search(r"title\s*: (.*)", text)
		val = match.group(1) if match else ""
		col = good if not_shit(val) or file_ext != '.mp3' else bad
		comm = "Название главы, как в оглавлении. Теги обязательны для mp3. В требованиях Эксмо-2023 указан устаревший id3v1 в кодировке Win-1251, но фактически следует проставлять id3v2 в юникоде."
		result += (('Тег title', val, col, comm), )
		
		#	artist          : Кристина Берндт
		match = re.search(r"artist\s*: (.*)", text)
		val = match.group(1) if match else ""
		col = good if not_shit(val) or file_ext != '.mp3' else bad
		comm = "Имя и фамилия автора/авторов"
		result += (('Тег artist', val, col, comm), )
		
		#	album           : Устойчивость. Как выработать иммунитет к стрессу, депрессии и выгоранию
		match = re.search(r"album\s*: (.*)", text)
		val = match.group(1) if match else ""
		col = good if not_shit(val) or file_ext != '.mp3' else bad
		comm = "Полное название книги"
		result += (('Тег album', val, col, comm), )
		
		#	album_artist    : Юлия Шустова
		match = re.search(r"album_artist\s*: (.*)", text)
		val = match.group(1) if match else ""
		col = good if not_shit(val) or file_ext != '.mp3' else bad
		comm = "Имя и фамилия диктора"
		result += (('Тег album artist', val, col, comm), )		
		
		#	genre           : Аудиокнига
		match = re.search(r"genre\s*: (.*)", text)
		val = match.group(1) if match else ""
		col = good if (val == "Аудиокнига") or (file_ext != '.mp3') else bad
		if (col == bad) and (val == "Audiobook"): col = compromise
		comm = "Всегда «Аудиокнига»"
		result += (('Тег genre', val, col, comm), )		
		
		#	track           : 000
		#	track           : 01/01
		match = re.search(r"track\s*: ([^/\n]*)", text)
		val = match.group(1) if match else ""
		col = good if (val == file_base) or file_ext != '.mp3' else bad
		if (col == bad) and val.isdigit() and file_base.isdigit() and (int(val) == int(file_base)): col = compromise
		comm = "Расставляются строго в порядке (001, 002)"
		result += (('Тег track', val, col, comm), )		
		
		#	date            : 2021
		match = re.search(r"date\s*: (.*)", text)
		val = match.group(1) if match else ""
		col = good if ((len(val) == 4) and (val.isdigit())) or file_ext != '.mp3' else bad
		comm = "Год сдачи готовой фонограммы"
		result += (('Тег date', val, col, comm), )		
		
		#Stream #0:0: Audio: mp3, 44100 Hz, mono, fltp, 128 kb/s
		#Stream #0:0: Audio: pcm_s24le ([1][0][0][0] / 0x0001), 48000 Hz, 1 channels, s32 (24 bit), 1152 kb/s
		match = re.search(r"Stream #0:0: Audio: ([^,]+), ([\d.]+) Hz, ([^,]+), [^,]+, ([\d]+) ", text)
		
		#val = match.group(1)
		#col = good if '.'+val == file_ext else bad
		#comm = ""
		#result += (('Кодек', val, col, comm), )	
		
		val = match.group(2)
		col = good if 44100 <= float(val) else bad
		comm = "Минимум 16 бит 44,1kHz"
		result += (('Частота дискретизации, Гц', val, col, comm), )	
		
		val = match.group(3)
		col = good if (val == 'stereo') or (val == '2 channels') else bad
		comm = "Формат звука - стерео (моно не принимается)"
		result += (('Каналы', val, col, comm), )	
		
		val = match.group(4)
		col = good if (val == '128') or file_ext != '.mp3' else bad
		comm = "Для mp3 битрейт — постоянный (constant), 128 Кбит/с."
		result += (('Битрейт', val, col, comm), )		
		
		# silence_start: 24.4189
		# silence_end: 25.6301 | silence_duration: 1.2112
		matches = re.findall(r"silence_end: ([\-\d\.]+) \| silence_duration: ([\-\d\.]+)", text)
		val = '<br>'.join([f"{m[1]} сек. на {datetime.timedelta(seconds=round(float(m[0])))}" for m in matches])
		col = bad if val else good
		comm = "Паузы строго до 5 сек."
		result += (('Тишина', val, col, comm), )	
		
		# Overall
		if (overall:=text.find("Overall")) != -1:
			text = text[overall:]
			
		# DC offset: -0.000001
		val = re.search(r"DC offset: ([\-\d\.]+)", text).group(1)
		col = bad if abs(float(val)) > 0.0005 else good  
		comm = "Смещение синусоиды вверх/вниз на 0,1% (0,001) в 16-бит файле вызовет щелчки амплитудой 32 (-54dB) в начале и конце файла. Не регламентируется Эксмо"
		result += (('Постоянное смещение', val, col, comm), )
		
		# Peak level dB: -5.814296
		val = re.search(r"Peak level dB: ([\-\d\.]+)", text).group(1)
		col = bad if float(val) >= -3 else good
		comm = "Максимальное пиковое значение -3dB"
		result += (('Макс. пик, дБ', val, col, comm), )	
		
		# RMS level dB: -22.339706
		val = re.search(r"RMS level dB: ([\-\d\.]+)", text).group(1)
		col = good if -23 < float(val) < -18 else bad
		comm = "Уровень звука по RMS от -23dB до -18dB"
		result += (('Интегральный RMS, дБ', val, col, comm), )	
		
		# Noise floor dB: -inf
		val = re.search(r"Noise floor dB: ([\-\d\.inf]+)", text).group(1)
		col = good if (val == '-inf') or (float(val) < -60) else bad
		comm = "Уровень шума не выше -60dB"
		result += (('Уровень шума, дБ', val, col, comm), )	
		
		# Entropy: 0.727892
		#val = re.search(r"Entropy: ([\-\d\.]+)", text).group(1)
		#col = neutral
		#comm = "Не вполне ясно, что это такое"
		#result += (('Энтропия', val, col, comm), )	
		
		# Bit depth: 32/32
		val = re.search(r"Bit depth: ([\-\d\.]+)", text).group(1)
		col = good if float(val) >=16 else bad
		comm = "Минимум 16 бит 44,1kHz"
		result += (('Битовая глубина', val, col, comm), )
		
		return result
	except: 
		print("Блин, всё же работало, чё за фигня? Программисты эти не могут нормально делать, чтоб без ошибок??")
		for n, v in locals().items():  print(f"{n}: {v}")
		raise

	
def decode(data):
	result = ()
	for s in data:
		try:
			result += ("\n".join(s.decode().splitlines()) if s else "",)
		except:
			result += ("\n".join(s.decode('cp866').splitlines()) if s else "",)
	return result	


async def run_ffmpeg(file, sem):
	async with sem:
		shortname = os.path.basename(file) # 001.mp3
		print(f"Анализирую {shortname} ...")
		cmd = f'ffmpeg -hide_banner -nostats -loglevel info -i "{file}" -af astats,silencedetect=n=-45dB:d=5 -vn -f null - 2>&1'
		proc = await asyncio.create_subprocess_shell(cmd, stdout=asyncio.subprocess.PIPE)
		stdout, stderr = decode(await proc.communicate())
		#proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE) 
		#stdout, stderr = decode(proc.communicate())
		if proc.returncode != 0: 
			print(f"Ошибка {proc.returncode} при попытке анализа {shortname}")
			print(f"{stderr} \n {stdout}")
		else: 
			print(f"Проанализирован {shortname}") 
		return parse_ffmpeg_output(stdout, shortname)


#   data[
#		(('Имя', '001.mp3', col, comm), ('Тишина', val, col, comm), ('Битрейт', '128', col, comm)),
#		(('Имя', '002.mp3', col, comm), ('Тишина', val, col, comm), ('Битрейт', '76', col, comm)), 
#		(('Имя', '003.mp3', col, comm), ('Тишина', val, col, comm), ('Битрейт', '320', col, comm))
#   ]   
def display_result(data):
	table = '<table>\n'
	# Заголовки
	table += ' <tr>\n'
	for param in data[0]: 
		table += f'  <th>{param[0]}</th>\n'
	table += ' </tr>\n'
	# Данные
	for file in data:
		table += ' <tr>\n'
		for param in file:
			table += f'  <td title="{param[3]}" class="{param[2]}">{param[1]}</td>\n'
		table += ' </tr>\n'
	table += '</table>\n'	
	# Пояснения
	for param in data[0]: 
		table += f' \n<p><b>{param[0]}:</b> {param[3]}</p>\n'
	css = "table, th, td{border:1px solid black; border-collapse: collapse; padding: 5px;} \
	       .g{background-color: PaleGreen} .b{background-color:Salmon} .c{background-color:#ffff73} \
		   .sm{font-size:small}"
	html = fr"<html><body><style>{css}</style><h1>Проверка на соответствие требованиям Эксмо</h1>{table}</body></html>"
	print(f'Открываю результаты в браузере...')
	with open(os.path.join(tempfile.gettempdir(), 'eksmo_check.html'), 'w', encoding='utf-8') as f:
		f.write(html)
		print('file://' + f.name)
	webbrowser.open_new_tab('file://' + f.name)


async def main(files):
	sem = asyncio.Semaphore(MAX_CONCURRENT_TASKS)
	tasks = []
	for file in files:
		async with sem:
			task = asyncio.create_task(run_ffmpeg(file, sem))
			tasks += [task]
	data = await asyncio.gather(*tasks)
	display_result(data)



# Считываем переданные имена файлов и папок
if len(sys.argv) > 1: files = [f.strip('\"') for f in sys.argv[1:]]
else: files = next(csv.reader([input(help_string)], delimiter=' ', quotechar='"'))

# Обходим папки не рекурсивно и чистим получившийся список файлов
for i in range(0, len(files)):
	if os.path.isdir(files[i]): files += [os.path.join(files[i], f) for f in os.listdir(files[i])]
files = [f for f in files if (os.path.isfile(f) and f.lower().endswith(('.wav', '.mp3', '.flac')))]

if not files: 
	input("Нет ни одного подходящего файла!")
	sys.exit(-1)
print(f'\nВсего {len(files)} файлов. Анализируем по {MAX_CONCURRENT_TASKS} одновременно.')

asyncio.run(main(files))

print('Готово.')


