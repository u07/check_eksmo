import subprocess
import pkg_resources

# Автоустановка недостающих модулей, чтобы не беспокоить пользователей
required = {'tkinter', }
installed = {pkg.key for pkg in pkg_resources.working_set}
if (missing := required - installed):
	print("\n\nПозвольте установить недостающие модули! Потребуется интернет. \n\n")
	python = sys.executable
	subprocess.check_call([python, '-m', 'pip', 'install', *missing])
	print("\nСпасибо за ожидание, теперь можем продолжить.\n")
	
import tkinter




import tkinter as tk

# Define data
data = [
    ["Name", "Age", "Color"],
    ["John", "32", "Blue"],
    ["Mary", "24", "Green"],
    ["Tom", "45", "Red"]
]

# Create table
root = tk.Tk()
for i, row in enumerate(data):
    for j, value in enumerate(row):
        label = tk.Label(root, text=value, borderwidth=2, relief="groove")
        if i == 0:
            label.config(bg="lightgray")
        elif j == 2:
            label.config(bg=value)
        label.grid(row=i, column=j, padx=5, pady=5)
root.mainloop()




stdout, stderr = await proc.communicate()

    print(f'[{cmd!r} exited with {proc.returncode}]')
	
	
	# -af astats=metadata=1:reset=1000,ametadata=print:file=- -f null -
	# -filter_complex ebur128
	# -filter_complex loudnorm=print_format=summary
	# -af astats=metadata=1:reset=10000000,ametadata=print:file=- -f null -