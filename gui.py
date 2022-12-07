import PySimpleGUI as sg	
import os 
import subprocess
import threading
import queue
import pyffish
import matplotlib.pyplot as plt
from dataclasses import dataclass
from contextlib import closing


@dataclass
class Setting():
	control =[
		[sg.Text('Engine 1'), sg.Push(), sg.Input(visible=False,key='engine_1'), sg.FileBrowse()],
		[sg.Text('Engine 2'), sg.Push(), sg.Input(visible=False,key='engine_2'),sg.FileBrowse()],
		[sg.Text('Variant'), sg.Push(), sg.Push(), sg.Input('chess',key='fsf_variant',size=(12,1)), sg.Button('select',key='fsf_variants')],
		[sg.Text('variants.ini (optional)'), sg.Push(), sg.Input(visible=False,key='variant.ini'),sg.FileBrowse()],
		[sg.Text('Engine 1 NNUE (optional)'), sg.Push(), sg.Input(visible=False,key='nnue_1'),sg.FileBrowse()],
		[sg.Text('Engine 2 NNUE (optional)'), sg.Push(), sg.Input(visible=False,key='nnue_2'),sg.FileBrowse()],
		[sg.Text('Book (optional)'),sg.Push(), sg.Input(visible=False,key='book'), sg.FileBrowse()],
		[sg.Text('total games'),sg.Push(),sg.Input('10',key='games',size=(13,1))],
		[sg.Text('time per game (ms)'),sg.Push(),sg.Input('10',key='time',size=(13,1))],
		[sg.Text('increment per move (ms)'),sg.Push(),sg.Input('1',key='i',size=(13,1))],
		[sg.Text()],
		[sg.Push(),sg.Button('GO',key='go'),sg.Push()],	
	]

	output =[
		[sg.Multiline(do_not_clear=True, autoscroll=True, size=(60, 20), key='engine_output')],
		[sg.Multiline(do_not_clear=True, autoscroll=True, size=(60, 10), key='result')],
		[sg.Text('export as bar chart'),sg.Push(),sg.Button('export', key='export'),sg.Push()]
	]

	layout = [[
		sg.Column(control),
		sg.TabGroup([[sg.Tab('Output',output)]])	
	]]

	window_looking = {
		"default_button_element_size": (12, 1),
		"auto_size_buttons": False,
		"font": ('Consolas',12),
		"resizable": True
	}

setting = Setting()


class Engine():
	def __init__(self,message):
		self.process = subprocess.Popen(message, 
										stdin=subprocess.PIPE,
										stdout=subprocess.PIPE,
										universal_newlines=True,
										bufsize=1,
										shell=True)

	def read(self):
		while self.process.poll() is None:            # make sure the child process is still alive
			yield self.process.stdout.readline()      

class GUI():
	'''main frame'''
	def __init__(self):
		self.window = sg.Window('Variant Fish Test', setting.layout, **setting.window_looking)	
		self.engine = None
		self.message = []
		self.pipe = queue.Queue()              # let producer keep reading info from subprocess, then thow it to pipe
		                                       # in order not to miss info when subprocess end and kill Pipe.

		self.producer_lock = threading.Lock()         # make sure only one thread is working at a time
		self.consumer_lock = threading.Lock()

	@staticmethod
	def popup(element, header, data, **kwargs):
		layout = [[element(data, key='ok', **kwargs)], [sg.Button('OK')]]
		with closing(sg.Window(header, layout, **setting.window_looking).finalize()) as window:
			while True:
				event, values = window.read()
				print(event,values)
				if event == sg.WINDOW_CLOSED or event == 'OK':
					if values and values['ok']:
						return values['ok']
					return

	@staticmethod
	def export_chart(info,variant):
		if len(info) == 1:
			info = info[0].strip().split(' ')
			print(info)
			y = [int(info[3]),int(info[5]),int(info[7])]
			x = ['win','lose','draw']
			plt.bar(x,y)
			plt.title(f'{variant} match, with {info[1]} games played')
			plt.show()
		else:
			pass

	def load_engine(self,command):
		self.message = []
		if self.engine:
			self.engine.process.terminate()
		with self.pipe.mutex:
			self.pipe.queue.clear()
		print('engine end')

		def producer():                        # keep catching info from subprocess
			with self.producer_lock:
				print('producer start')
				for line in self.engine.read():
					self.pipe.put(line)
					print('ADD : add {} into queue'.format(line.strip() if line != "\n" else line))
				print('engine end')
				print(f'there are still {self.pipe.qsize()} line need to be processed')
				print('producer end')
		
		def consumer():                        # read from pipe and blit it on screen
			with self.consumer_lock:
				print('consumer start')
				counter = 0; flag = 0; start_count = False
				try:
					while not self.pipe.empty() or self.engine.process.poll() is None:
						line = self.pipe.get()
						self.message.append(line)
						self.window['engine_output'].update(''.join(self.message))
						print(f'SET : {line.strip()} from queue',flush=True)
						if line.startswith('-----'):
							flag += 1
						if flag == 2:
							start_count = True
						if start_count:
							counter += 1
							if counter == 8:
								break
				except RuntimeError:
					pass
				self.window['result'].update(''.join(self.message[-7:]))
				print('consumer end')
				
		with self.consumer_lock:                       # gain the lock when threads all end
			with self.producer_lock:
				print('engine start')
				print(f'there are {threading.active_count()} thread running')
				self.engine = Engine(command)
				self.producer_thread = threading.Thread(target=producer, daemon=True)
				self.consumer_thread = threading.Thread(target=consumer, daemon=True)
				self.producer_thread.start(); self.consumer_thread.start()

	def go(self, engine_1, variant , engine_2=None, ini=None, nnue_1=None, nnue_2=None, book=None, total_games=None, time=None, increment=None):
		command = 'python -u {} {} {} {}{}{}{}{}{}{}{} \n'       # -u specify buffsize = 0

		if not engine_1 or not engine_1.endswith('.exe'):
			self.popup(sg.Text, 'Please Check', 'Please at least select an engine for engine 1. If engine 2 is not specified, it will do engine 1 self match.',size=(50, 3))
		
		else:
			command = command.format(
				os.path.dirname(os.path.abspath(__file__)) + '\\variantfishtest.py',
				engine_1,
				engine_2 if engine_2 else engine_1,
				' -v '+variant,
				' -c '+ini if ini else '', 
				' --e1-options EvalFile='+nnue_1 if nnue_1 else '',
				' --e2-options EvalFile='+nnue_2 if nnue_2 else '',
				' -b '+book if book else '', 
				' -n '+total_games if total_games else '', 
				' -t '+time if time else '',
				' -i '+increment if increment else '',	 
			)
			print(command)
			self.window['engine_output'].update(f'> {command}\nstart \n{"="*20}')
			self.load_engine(command)

	def start(self):
		while True:
			event, values = self.window.read() 
			print(event, values)	   
			if event == sg.WIN_CLOSED or event == 'Exit':
				break	  

			elif event == 'fsf_variants':
				variant = self.popup(sg.Listbox, 'variant',pyffish.variants(),size=(30,20))
				if variant:
					self.window['fsf_variant'].update(variant[0]) 

			elif event == 'go':
				self.window['engine_output'].update(''); self.window['result'].update('')
				self.go(engine_1 = values['engine_1'],
						engine_2 = values['engine_2'],
						variant = str(values['fsf_variant']).strip() if values['fsf_variant'] else 'chess',
						ini = values['variant.ini'],
						nnue_1 = values['nnue_1'],
						nnue_2 = values['nnue_2'],
						book = values['book'],
						total_games = values['games'],
						time = values['time'],
						increment = values['i'])
						
			elif event == 'export':
				if not self.message:
					pass
				else:
					print(self.message[-1:])
					self.export_chart(self.message[-1:],values['fsf_variant'].strip())

		self.window.close()
		return

if __name__ == '__main__':
	fishtest = GUI()
	fishtest.start()
