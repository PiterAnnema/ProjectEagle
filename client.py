from serial import Serial
import threading
import time

class SerialHandler():
	def __init__(self, port=None, baud=None):
		self.port = port
		self.baud = baud

		self.connection = None

		self.connectSerial()


	def connectSerial(self):
		while True:
			try:
				print('Connecting', self.port, self.baud)
				self.connection = Serial(self.port, self.baud)
			except Exception as e:
				print(e)
				prompt = SerialPrompt(self.port, self.baud)
				self.port = prompt.port
				self.baud = prompt.baud
			else:
				break


	def startMonitor(self, callback, *args, **kwargs):
		self.monitor = threading.Thread(target=self.serialMonitor, args=(callback,*args), kwargs=kwargs)
		self.monitor.start()


	def serialMonitor(self, callback, *args, **kwargs):
		while True:
			line = self.connection.readline().decode().strip()
			callback(line, *args, **kwargs)
	


class TourGame():
	def __init__(self, name, n_players=28):
		self.name = name
		self.finished = []

	def finish(self, player, time):
		print('finish', player, time)
		self.finished.append((player, time))


	def start(self):
		print('starting', self.name)
		self.state = True


	def stop(self):
		print('stopping', self.name)
		self.state = False



class Tour():
	def __init__(self):
		self.game = None

		self.serial_conn = SerialHandler('COM4', 115200)
		self.serial_conn.startMonitor(self.processSerial, name='Hello')


	def processSerial(self, line: str, name = 'SERIAL'):
		data = line.split(' ')
		code = data[0]
		value = None
		if len(data) > 1:
			value = data[1]

		if code == 'FIN':
			player, time = value.split(':')
			self.game.finish(player, time)
		elif code == 'GMT':
			print('gametime', value)
			
		print(code, value)


	def startGame(self):
		self.game.start()


	def stopGame(self):
		self.game.stop()
		print(self.game.finished)


	def newGame(self, name):
		self.game = TourGame(name)


def main():
	tour = Tour()
	tour.newGame('round1')
	while True:
		print('.')

		time.sleep(1)
		tour.serial_conn.connection.write(b'r')

		time.sleep(2)
		tour.serial_conn.connection.write(b's')

		time.sleep(2)
		tour.serial_conn.connection.write(b't')


if __name__ == '__main__':
	main()
