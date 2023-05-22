import mutagen

audio = mutagen.File(input('Drop your Mp3 here').strip('"'))

if audio:
	print(audio.info.pprint())
	if audio.info.mode == 1: print('joint stereo')
	if audio.info.mode == 0: print('true stereo')
	#print(audio.tags.pprint())
	print("Available metadata:")
	for key in audio.keys():
		val = str(audio.get(key, ['']))[:150].replace('\n',' ').replace('\r',' ')
		enc = audio[key].encoding if hasattr(audio[key], 'encoding') else ""
		print(f" {key} {enc} === {val}")
		
else:
	print("No Data here, just us")