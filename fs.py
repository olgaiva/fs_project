# Olga Ivanova ID 999084690 Winter 2017 ECS 145

# fs.py, the module which contains all the classes and functions
# associated with the file system fs

import os
import mmap

class fs:
	def __init__(self, str):
		self.name = str

		size = os.path.getsize(self.name)

		# number of bytes which are free in the system
		self.freespace = size

		# numbers of the bytes which are available for allocating
		self.freebytes = range(0, size)

		# open file descriptors
		self.freefd = range(0,1000)

		# file descriptor table
		self.fdtable = {}

		# file position table
		self.fpostable = {}

		# file length table
		self.flength = {}

		# Initialize root directory
		self.root = directory('root')

		self.currentDir = self.root


	def create(self, filename, nbytes):
		# File pathname stuff
		dir_list = filename.split('/')

		if (dir_list[0] == 'root') and (len(dir_list) == 1):
			parentDir = self.root

		elif dir_list[0] == 'root':
			parentDir = self.root.find(dir_list)
		else:
			dir_list.insert(0, self.currentDir.name)
			parentDir = self.currentDir.find(dir_list)

		bytes = int(nbytes)

		# checks first to see if there is space available
		try:
			if bytes > self.freespace:
				raise ValueError
			else:
				# creates new file
				filename = dir_list[-1]
				new_file = file(filename)
				parentDir.listfiles.append(new_file)

				# Trying to use mmap python module to make file i/o easier
				# Not sure if this will make changes in the actual file? -> use flush
				native_file = open(self.name, 'r+')
				mm = mmap.mmap(native_file.fileno(), 0, access=mmap.ACCESS_WRITE)

				byte_tuple = []
				# allocate space
				for i in range(0, bytes):
					byte_tuple.append(self.freebytes[0])
					mm[self.freebytes[0]] = '\x00'
					del self.freebytes[0]
					self.freespace -= 1

				new_file.listbytes = tuple(byte_tuple)
			
			# flush, close mmap and file
			mm.flush()
			mm.close()
			native_file.close()

		except ValueError:
			print "There is not enough space available for a file of this size."

		

	def open(self, filename, mode):
		try:
			# File pathname stuff
			dir_list = filename.split('/')

			if (dir_list[0] == 'root') and (len(dir_list) == 1):
				parentDir = self.root

			elif dir_list[0] == 'root':
				parentDir = self.root.find(dir_list)
			else:
				dir_list.insert(0, self.currentDir.name)
				parentDir = self.currentDir.find(dir_list)

			filename = dir_list[-1]

			if (parentDir == None):
				raise KeyError

			else:
				my_file = None
				for f in parentDir.listfiles:
					if f.name == dir_list[-1]:
						my_file = f

				if my_file == None:
					raise KeyError

				
				# add filename, initial position
				my_file.pos = 0

				# set file length to 0 (nothing written)
				my_file.length = 0

				# assign file descriptor
				fd = self.assign_fd(my_file, mode)
				return fd

		except KeyError:
			print "File not found."

	# Helper function for open()
	def assign_fd(self, file, mode):
		if mode == 'r':
			for i in self.freefd:
				if i % 2 == 0:
					self.fdtable[i] = file
					self.freefd.remove(i)
					return	i
		elif mode == 'w':
			for i in self.freefd:
				if i % 2 != 0:
					self.fdtable[i] = file
					self.freefd.remove(i)
					return	i		
		return 1000

	def close(self, fd):
		file = self.fdtable[fd]
		
		# Must first return the fd to the list of free fds
		self.freefd.append(fd)

		del self.fdtable[fd]
		file.pos = None


	def pos(self, fd):
		file = self.fdtable[fd]
		return file.pos

	def length(self, fd):
		file = self.fdtable[fd]
		return file.length

	def seek(self, fd, pos):
		file = self.fdtable[fd]
		try:
			if pos < 0:
				raise TypeError
			elif pos >= len(file.listbytes):
				raise IndexError
			elif pos == file.pos:
				return
			else:
				# check for contiguity of bytes
				
				if pos > file.pos:
					for i in range(file.pos, pos):
						curr_byte = file.listbytes[i]
						next_byte = file.listbytes[i+1]
						if (next_byte - curr_byte) > 1:
							raise ValueError
				else:
					for i in range(pos, file.pos):
						curr_byte = file.listbytes[i]
						next_byte = file.listbytes[i+1]
						if (next_byte - curr_byte) > 1:
							raise ValueError
			
			# Finally, after checking everything, change pos
			file.pos = pos	
					

		except TypeError:
			print "Invalid file position - argument is negative."

		except IndexError:
			print "Invalid file position - argument is greater than file size."

		except ValueError:
			print "Selected file position is not contiguous to current file position."

	
	def read(self, fd, nbytes):
		n = int(nbytes)
		file = self.fdtable[fd]

		# Must return exception if the file is open in write mode
		try:
			if fd % 2 != 0:
				raise IOError	

			elif n > (len(file.listbytes) - file.pos):
				raise IndexError
			
			else:
				# String (currently a mutable list) which will be returned
				byte_list = []

				native_file = open(self.name, 'r+')
				mm = mmap.mmap(native_file.fileno(), 0, access=mmap.ACCESS_READ)

				# Start at current position
				curr_pos = file.pos
				for i in range(curr_pos, curr_pos + n):
					byte = file.listbytes[i]
					byte_list.append(mm[byte])

				mm.close()
				native_file.close()

				# Change the file's position
				file.pos += n

				# 'Stringify' list
				str_buffer = ''.join(byte_list)

				return str_buffer

		except IOError:
			print "File is currently in write mode. Read failed."

		except IndexError:
			print "Invalid read length - extends past EOF."


	def write(self, fd, writebuf):
		n = len(writebuf)
		file= self.fdtable[fd]
		
		# Must return exception if the file is open in write mode
		try:
			if fd % 2 == 0:
				raise IOError	

			elif n > (len(file.listbytes) - file.pos):
				raise IndexError
			
			else:
				# Add to flength - number of bytes used in file
				file.length += n
				
				# Split the writebuf to enable writing individual chars
				byte_list = list(writebuf)

				native_file = open(self.name, 'r+')
				mm = mmap.mmap(native_file.fileno(), 0, access=mmap.ACCESS_WRITE)

				# Start at current position
				curr_pos = file.pos
				for i in range(curr_pos, curr_pos + n):
					byte = file.listbytes[i]
					mm[byte] = byte_list[i - curr_pos]
					
				mm.flush()
				mm.close()
				native_file.close()

				# Change file's position
				file.pos += n


		except IOError:
			print "File is currently in read mode. Write failed."

		except IndexError:
			print "Invalid write length - extends past EOF."	

	def delfile(self, filename):
		try:
			# File pathname stuff
			dir_list = filename.split('/')

			if (dir_list[0] == 'root') and (len(dir_list) == 1):
				parentDir = self.root

			elif dir_list[0] == 'root':
				parentDir = self.root.find(dir_list)
			else:
				dir_list.insert(0, self.currentDir.name)
				parentDir = self.currentDir.find(dir_list)

			filename = dir_list[-1]

			if (parentDir == None):
				raise KeyError

			else: 
				my_file = None
				for f in parentDir.listfiles:
					if f.name == dir_list[-1]:
						my_file = f

				if my_file == None:
					raise KeyError

				elif my_file.pos != None:
					raise OSError
				
				else:
					self.freespace += len(my_file.listbytes)
					self.freebytes.extend(my_file.listbytes)
					parentDir.listfiles.remove(my_file)	

		except KeyError:
			print "File not found."
	
		except OSError:
			print "File is currently open. Delete failed."

	def mkdir(self, str):
		try:
			# Split the path into tokens using the '/' char, if there are any
			dir_list = str.split('/')


			if (dir_list[0] == 'root') and (len(dir_list) == 1):
				parentDir = self.root

			elif dir_list[0] == 'root':
				parentDir = self.root.find(dir_list)
			else:
				dir_list.insert(0, self.currentDir.name)
				parentDir = self.currentDir.find(dir_list)

			for d in parentDir.listdirs:
				if d.name == dir_list[-1]:
					raise OSError

			dir = directory(dir_list[-1])
			parentDir.listdirs.append(dir)
			
		except OSError:
			print "Cannot create directory - directory already exists."

	def isdir(self, str):
		dir_list = str.split('/')

		if (dir_list[0] == 'root') and (len(dir_list == 1)):
			return True

		elif dir_list[0] == 'root':
			parentDir = self.root.find(dir_list)
		
		else:
			dir_list.insert(0, self.currentDir.name)
			parentDir = self.currentDir.find(dir_list)

		if parentDir == None:
			return False

		for d in parentDir.listdirs:
			if d.name == dir_list[-1]:
				return True

		return False

	def listdir(self, str):
		dir_list = str.split('/')
		
		if (dir_list[0] == 'root') and (len(dir_list) == 1):
			listed_dir = self.root

		elif dir_list[0] == 'root':
			parentDir = self.root.find(dir_list)
			for d in parentDir.listdirs:
				if d.name == dir_list[-1]:
					listed_dir = d
		
		else:
			dir_list.insert(0, self.currentDir.name)
			parentDir = self.currentDir.find(dir_list)

			for d in parentDir.listdirs:
				if d.name == dir_list[-1]:
					listed_dir = d

		list_ls = []

		for d in listed_dir.listdirs:
			list_ls.append(d.name)
	
		for f in listed_dir.listfiles:
			list_ls.append(f.name)

		return list_ls


	def chdir(self, str):
		dir_list = str.split('/')

		if (dir_list[0] == 'root') and (len(dir_list) == 1):
			self.currentDir = self.root

		elif dir_list[0] == 'root':
			parentDir = self.root.find(dir_list)
			for d in parentDir.listdirs:
				if d.name == dir_list[-1]:
					self.currentDir = d
		
		else:
			dir_list.insert(0, self.currentDir.name)
			parentDir = self.currentDir.find(dir_list)

			for d in parentDir.listdirs:
				if d.name == dir_list[-1]:
					self.currentDir = d


	def deldir(self, str):
		try:
			dir_list = str.split('/')
			
			dir_to_delete = None
			if dir_list[0] == 'root':
				parentDir = self.root.find(dir_list)
				for d in parentDir.listdirs:
					if d.name == dir_list[-1]:
						dir_to_delete = d
		
			else:
				dir_list.insert(0, self.currentDir.name)
				parentDir = self.currentDir.find(dir_list)

				for d in parentDir.listdirs:
					if d.name == dir_list[-1]:
						dir_to_delete = d
			
			if dir_to_delete == None:
				raise LookupError
	
			elif dir_to_delete == self.currentDir:
				raise OSError

			bad_delete = dir_to_delete.contains(self.currentDir)
			if (True in bad_delete):
				raise OSError

			else:
				freed_bytes = dir_to_delete.delete()
				self.freespace += len(freed_bytes)
				self.freebytes.extend(freed_bytes)
				parentDir.listdirs.remove(dir_to_delete)
				

		except LookupError:
			print "Directory not found."

		except OSError:
			print "Calling process is within specified directory. Delete failed."



# Separate class for directory
# Should at minimum contain:
# List of directory names
# List of files that are in that directory

class directory:
	def __init__(self, str):
		self.name = str
		self.listdirs = []
		self.listfiles = []

	# Helper function for the dir functions
	def find(self, dir_list):
		if len(dir_list) == 2:
			return self

		for dir in self.listdirs:
			if dir.name == dir_list[1]:
				dir_list.remove(dir_list[0])
				return dir.find(dir_list)
		return None

	# Helper function for deleting a directory
	def delete(self):
		freed_bytes = []
		for f in self.listfiles:
			freed_bytes.extend(f.listbytes)
			self.listfiles.remove(f)
		for dir in self.listdirs:
			freed_bytes.extend(dir.delete())
			self.listdirs.remove(dir)
		return freed_bytes
			
	# Determines if one directory contains another

	def contains(self, dir):
		bad_delete = []
		if (dir in self.listdirs):
			bad_delete.append(True)
			return bad_delete
		else:
			for d in self.listdirs:
				bad_delete.extend(d.contains(dir))
				
		return bad_delete


class file:
	def __init__(self, str):
		self.name = str
		self.listbytes = ()
		self.length = 0
		self.pos = None


def init(str):
	return fs(str)