#!/usr/bin/python3

class IRCBotException(Exception):
    pass

class IRCBot:

    MAX_BUFSIZE = 10240

    def __init__(self, server, port, ssl=False):
        import socket, ssl
        self.server = server
        self.port   = port
        if ssl:
            self.sock = ssl.wrap_socket(socket.socket(socket.AF_INET, socket.SOCK_STREAM))
        else:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.channel = None
        self.buffer = b''
        self.lines_buffer = []

    def connect(self):
        self.sock.connect((self.server, self.port))
        return self

    def identify(self, nickname, password=None):
        self.sock.send('USER {0} {0} {0} :{0}\r\n'.format(nickname).encode('utf8'))
        self.sock.send('NICK {0}\r\n'.format(nickname).encode('utf8'))
        if password: self.sock.send('PRIVMSG NICKSERV :IDENTIFY {0}\r\n'.format(password).encode('utf8'))
        return self

    def join(self, channel):
        self.channel = channel
        self.sock.send('JOIN {0}\r\n'.format(channel).encode('utf8'))
        return self

    def leave(self):
        self.sock.send('PART {0}\r\n'.format(self.channel).encode('utf8'))
        self.channel = None
        return self

    def quit(self):
        self.sock.send('QUIT\r\n'.encode('utf8'))
        self.sock.close()
        return self

    def _recv(self, buffer_size=2048):
        recv_data = self.sock.recv(buffer_size)
        recv_size = len(recv_data)
        self.buffer += recv_data
        if len(self.buffer) > self.MAX_BUFSIZE:
            raise IRCBotException('max buffer size reached')
        while True:
            if self.buffer.find(b'\r\n') != -1:
                line, self.buffer = self.buffer.split(b'\r\n', 1)
                line_str = line.decode('utf8')
                self.lines_buffer.append(line_str)
                if line_str.startswith('PING :'):
                    self._pong(line_str)
            else:
                break
        return recv_size

    def readline(self):
        self._recv()
        if self.lines_buffer:
            return self.lines_buffer.pop(0)
        else:
            return ''

    def readlines(self, buffer_size=2048):
        self._recv()
        if self.lines_buffer:
            result_lines = self.lines_buffer[:]
            self.lines_buffer = []
            return result_lines
        else:
            return []

    def writeline(self, msg):
        return self.sock.send('PRIVMSG {0} :{1}\r\n'.format(self.channel, msg).encode('utf8'))

    def writelines(self, msg_list):
        sent_bytes = 0
        for msg in msg_list:
            sent_bytes += self.sock.send('PRIVMSG {0} :{1}\r\n'.format(self.channel, msg).encode('utf8'))
        return sent_bytes

    def _pong(self, line):
        return self.sock.send('PONG :{0}\r\n'.format(line.split(':', 1)[1]).encode('utf8'))

if __name__ == '__main__':
    import sys
    server   = sys.argv[1]
    port     = int(sys.argv[2])
    nickname = sys.argv[3]
    password = sys.argv[4]
    channel  = sys.argv[5]
    ircbot = IRCBot(server, port).connect()
    ircbot.identify(nickname, password)
    ircbot.join(channel)
    while True:
        for line in ircbot.readlines():
            print(line)
            if '!bot quit' in line:
                ircbot.writeline('Got it, sir!!')
                ircbot.leave()
                ircbot.quit()
                sys.exit(0)
