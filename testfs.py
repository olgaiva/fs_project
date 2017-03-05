# Olga Ivanova ID 999084690 Winter 2017 ECS 145
import sys
import fs

def main():
	filesystem = fs.init('abc')
	filesystem.mkdir('boop')
	filesystem.create('x', 4)
	filesystem.create('y', 8)
	fd = filesystem.open('x', 'w')
	pos_fd = filesystem.pos(fd)
	print pos_fd
	length_fd = filesystem.length(fd)
	print length_fd
	filesystem.seek(fd, 3)
	pos_fd = filesystem.pos(fd)
	print pos_fd
	filesystem.seek(fd, 0)
	filesystem.write(fd, 'blah')
	filesystem.close(fd)
	filesystem.chdir('boop')
	fd = filesystem.open('x', 'w')
	filesystem.mkdir('root/boop/boopity')
	print filesystem.isdir('boopity')
	print filesystem.listdir('root')
	filesystem.delfile('x')
	filesystem.chdir('boopity')
	filesystem.deldir('root/boop')
	filesystem.chdir('root')
	print filesystem.listdir('root')
	

	
	

if __name__ == '__main__': main()