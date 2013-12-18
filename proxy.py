#!/usr/bin/env python

import sys
import md5
import httplib
import gzip
import urlparse
import SimpleHTTPServer
import BaseHTTPServer
import SocketServer

class Handler(BaseHTTPServer.BaseHTTPRequestHandler):
	protocol_version = "HTTP/1.1"

	def transform(self, url, data):
		return data

	def send_response(self, code, message):
		self.log_request(code)
		self.wfile.write("%s %d %s\r\n" % (self.protocol_version, code, message))

	def data_write(self, digest, name, content):
		o = open('d/' + digest + '.' + name, 'w')
		o.write(content)
		o.close()


	def do(self, method):
		self.close_connection = 1
		params = None
		headers_out = {}
		content_length = 0
		commpression = 'None'

		# Extract Headers from request
		for head in self.headers:
			vhead = head
			if head == 'proxy-connection':
				vhead = 'Connection'
			if head == 'content-length':
				content_length = int(self.headers.get(head))
			if head in ('host'):
				continue
			headers_out[vhead.title()] = self.headers.get(head)

		# Extract POST body
		if content_length > 0:
			params = self.rfile.read(content_length)
			
		#sys.stderr.write(str(headers_out) + '\n')
	
		# parse request
		url = urlparse.urlparse(self.path)
		"""
			http://www:71/content/img.jpg?b=1#TOP
			scheme='http'
			netloc='www:71'
			path='/content/img.jpg'
			params=''
			query='b=1'
			fragment='TOP'
		"""

		# send request
		conn = httplib.HTTPConnection(url.netloc)
		conn.request(method, url.path, params, headers_out)

		# get responce
		response = conn.getresponse()
		headers_in = response.msg.headers
		self.send_response(response.status, response.reason)

		# set headers
		#sys.stderr.write(str(headers_in) + '\n')
		for head_line in headers_in:
			head, value = head_line.split(':', 1)
			head = head.strip()
			value = value.strip()
			if head in ('Transfer-Encoding'):
				continue
			if head == 'Connection':
				value = 'close'
			if head == 'Content-Encoding':
				commpression = value
				continue
			self.send_header(head.title(), value)

		self.end_headers()

		# send data
		data = response.read()
	
		# write file
		m = md5.new(data).hexdigest()
		self.data_write(m, 'url', self.path)
		self.data_write(m, 'dat', data)
		self.data_write(m, 'hin', str(headers_in))
		self.data_write(m, 'hou', str(headers_out))
		self.data_write(m, 'pos', str(params))

		if commpression == 'gzip':
			data = gzip.decompress(data)
		elif commpression == 'None':
			pass
		else:
			sys.stderr.write('Unknown compression\n')
			return False
		data = transform(self.path, data)
	
		self.wfile.write(data)
		return False

	def do_GET(self):
		self.do('GET')

	def do_POST(self):
		self.do('POST')

	def do_HEAD(self):
		self.do('HEAD')

class ThreadedHTTPServer(SocketServer.ThreadingMixIn, BaseHTTPServer.HTTPServer):
	pass

def main():
	server_address = ('127.0.0.1', 8089)
	httpd = ThreadedHTTPServer(server_address, Handler)
	httpd.serve_forever()

if __name__ == '__main__':
	main()
