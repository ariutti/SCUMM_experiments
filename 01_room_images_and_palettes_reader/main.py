# ref: room resources (Scumm V1) - https://wiki.scummvm.org/index.php?title=SCUMM/Technical_Reference/Room_resources
# I'm interested in room images so
# ref (image resources): https://wiki.scummvm.org/index.php?title=SCUMM/Technical_Reference/Image_resources
# ref (image resources - version 5 specific): https://web.archive.org/web/20090727144325/http://scumm.mixnmojo.com/?page=articles/article1

# ref: a tool to extract all of LucasArts game resources is LucasRipper (downloadable from here: https://web.archive.org/web/20081222140420/http://scumm.mixnmojo.com/?page=downloads)

from io import BytesIO
import os

# I'm actually placing my game files in the parent folder
FILE_001 = "ATLANTIS.001"

PALETTE_FOLDER = "palettes"
SAVE_PALLETES  = True
PALETTE_IMAGE_SCALE_FACTOR = 16

BACKGROUND_IMAGES_FOLDER = "backgrounds"
SAVE_BACKGROUND_IMAGE = True
BACKGROUND_IMAGE_SCALE_FACTOR = 2

# don't touch below ************************************************************
def intToHex( value, num_bytes=1):
	return f"{value.to_bytes(num_bytes, byteorder='big').hex().upper()}"

def xor(file_path, xor_key=0x69):
	try:
		# Read file content and decode every bytes
		with open(file_path, 'rb') as file:
			content = file.read()
		# Decode all the file content xoringit with 0x69
		decoded = bytes([b ^ xor_key for b in content])
		return decoded
	except FileNotFoundError:
		print(f"File {file_path} not found.")
		return None
	except Exception as e:
		print(f"Error: {e}")
		return None

def readBlockHeader(file, byteOrder='big'):
	# read first 4 bytes for the block name
	block_name_bytes = file.read(4)
	block_name = block_name_bytes.decode('ascii')
	# read next 4 bytes for block size (Big Endian)
	block_size_bytes = file.read(4)
	block_size = int.from_bytes(block_size_bytes, byteOrder)
	#print(f"Block Name: {block_name} - Block Size: {block_size}")
	return block_name, block_size

# ******************************************************************************
from PIL import Image
def drawCLUT( filename, COLOR_LIST, width, height, scale_factor):
	image = Image.new("RGB", (width, height), "black")  # Default to black background
	# Load the pixel map
	pixels = image.load()
	# Set pixel colors
	for y in range(height):
		for x in range(width):
			index = x + (y*width)
			pixels[x, y] = COLOR_LIST[ index ]

	# Calculate new dimensions
	new_width = image.width * scale_factor
	new_height = image.height * scale_factor

	# Resize using nearest neighbor (no antialiasing)
	scaled_image = image.resize((new_width, new_height), Image.NEAREST)

	# Save and show the scaled image
	scaled_image.save( filename )
	#scaled_image.show()


"""
#ref: https://web.archive.org/web/20090727144325/http://scumm.mixnmojo.com/?page=articles/article1
# IMAGE COMPRESSION TABLE ******************************************************
IDs 			Method 			Rendering Direction 	Transparent 	Param Subtraction 	Remarks
0x01 			Uncompressed 	Horizontal 				No 				-			 		-
0x0E .. 0x12 	1st method 		Vertical 				No 				0x0A			 	-
0x18 .. 0x1C 	1st method 		Horizontal 				No 				0x14			 	-
0x22 .. 0x26 	1st method 		Vertical 				Yes 			0x1E			 	-
0x2C .. 0x30 	1st method 		Horizontal 				Yes 			0x28			 	-
0x40 .. 0x44 	2nd method 		Horizontal 				No 				0x3C			 	-
0x54 .. 0x58 	2nd method 		Horizontal 				Yes 			0x51			 	-
0x68 .. 0x6C 	2nd method 		Horizontal 				Yes 			0x64			 	Same as 0x54 .. 0x58
0x7C .. 0x80 	2nd method 		Horizontal 				No 				0x78			 	Same as 0x40 .. 0x44

"""
def getDecoderSettings( compressionId ):
	method    = None
	direction = None
	transparent = None
	parSub = None

	if compressionId == 0x01:
		method      = "Uncompressed"
		direction   = "Horizontal"
		transparent = "No"
		parSub      = 0
	elif compressionId >= 0x0E and compressionId <= 0x12:
		method      = "1st"
		direction   = "Vertical"
		transparent = "No"
		parSub      = 0x0A
	elif compressionId >= 0x18 and compressionId <= 0x1C:
		method      = "1st"
		direction   = "Horizontal"
		transparent = "No"
		parSub      = 0x14
	elif compressionId >= 0x22 and compressionId <= 0x26:
		method      = "1st"
		direction   = "Vertical"
		transparent = "Yes"
		parSub      = 0x1E
	elif compressionId >= 0x2C and compressionId <= 0x30:
		method      = "1st"
		direction   = "Horizontal"
		transparent = "Yes"
		parSub      = 0x28
	elif compressionId >= 0x40 and compressionId <= 0x44:
		method      = "2nd"
		direction   = "Horizontal"
		transparent = "No"
		parSub      = 0x3C
	elif compressionId >= 0x54 and compressionId <= 0x58:
		method      = "2nd"
		direction   = "Horizontal"
		transparent = "Yes"
		parSub      = 0x51
	elif compressionId >= 0x68 and compressionId <= 0x6C:
		method      = "2nd"
		direction   = "Horizontal"
		transparent = "Yes"
		parSub      = 0x64
	elif compressionId >= 0x7C and compressionId <= 0x80:
		method      = "2nd"
		direction   = "Horizontal"
		transparent = "No"
		parSub      = 0x78

	return (method,direction,transparent,parSub)


class BitReaderLSB:
	def __init__(self, byte_stream):

		self.stream = byte_stream
		self.current_byte = 0           # Byte actually beeing read
		self.bit_position = 8           # bit position (8 means load a new byte)

	def read_bit(self):
		if self.bit_position == 8:      # if all the bit of the current byte have been read
			byte = self.stream.read(1)  # Read the next byte
			if not byte:                # if we don't have no more availalbe bytes
				raise EOFError("End of stream")
			self.current_byte = ord(byte)  # get the byte as integer
			self.bit_position = 0          # Reset bit position

		# Extract current least significative bit
		bit = (self.current_byte >> self.bit_position) & 1
		#print(f"read bit {bit}")
		self.bit_position += 1
		return bit

	def read_bits(self, n):
		# read n bit and return them as an integer
		# with the last bit read ad LSB.
		value = 0
		for i in range(n):
			bit = self.read_bit()
			# Place every bit which has been read in the correct position (last bis as LSB)
			value |= (bit << i)
		return value

class StripeImageWriter:
	def __init__(self, w, h):
		self.width = w
		self.height = h
		# strip offset is a variable to keep track of the
		# horizontal position of the current stripe
		self.stripOffset = 0
		# x is always moving between 0 and 7 (8 pixels)
		self.x = 0
		# y is moving between 0 and height
		self.y = 0
		self.color = None
		self.image = Image.new("RGB", (self.width, self.height), "black")  # Default to black background
		# Load the pixel map
		self.pixels = self.image.load()
		self.pixelPerStripDrawn = 0

	def write_pixel(self, stripeID, color, number, direction):
		self.color = color
		counter = 0

		while counter < number:
			#print(f"strip {stripeID}, drawing pixel at position {self.stripOffset+self.x}x{self.y}")
			# first draw the current colore to the corrent x, y position
			self.pixels[ self.stripOffset+self.x, self.y] = self.color

			# then move the pixel position (taking care of wrapping accordingly to the directions)
			self.pixelPerStripDrawn += 1
			#print(f"strip {stripeID}, Drawn {self.pixelPerStripDrawn} in current strip")
			counter += 1
			if direction == "Horizontal":
				self.y = int(self.pixelPerStripDrawn / 8)
				self.x = self.pixelPerStripDrawn % 8
				#print(f"strip {stripeID}, horizontal movement: changing pen position to {self.stripOffset+self.x}x{self.y}")
			else:
				# vertical
				self.x = int(self.pixelPerStripDrawn / self.height)
				self.y = self.pixelPerStripDrawn % self.height
				#print(f"strip {stripeID}, Vertical movement: changing pen position to {self.stripOffset+self.x}x{self.y}")

	def moveToNextStrip(self):
		#print("\nmoving to next Strip")
		self.pixelPerStripDrawn = 0
		self.stripOffset += 8
		self.x = 0
		self.y = 0

	def save(self, filename, SCALE_FACTOR):
		# Calculate new dimensions
		new_width = self.image.width * SCALE_FACTOR
		new_height = self.image.height * SCALE_FACTOR

		# Resize using nearest neighbor (no antialiasing)
		self.scaled_image = self.image.resize((new_width, new_height), Image.NEAREST)
		self.scaled_image.save( filename )


def readRoomData(file, size, room_number, room_abs_offset, current_dir):
	counter = 0
	print( f"Reading room data for room number {room_number}, abs offset {room_abs_offset} - expected size is {size}" )

	# general variables for the current room (wiil be filled reading the room data)
	width    = 0
	height   = 0
	num_objs = 0
	room_cycles = []
	trasparent_index = None
	num_z_planes = 0
	COLOR_LOOKUP_TABLE = []
	BACKGROUND_IMAGE = None

	while counter < size-8:
		block_name, block_size = readBlockHeader(file)
		counter += 8

		# RMHD *****************************************************************
		# contains: width, height, number of objsects
		if block_name == "RMHD":
			width = file.read(2)
			width = int.from_bytes( width, byteorder='little', signed=False)

			height = file.read(2)
			height = int.from_bytes( height, byteorder='little', signed=False)

			num_objs = file.read(2)
			num_objs = int.from_bytes( num_objs, byteorder='little', signed=False)

			print( f"Room has {width}x{height} pixels dimension and {num_objs} number of objects inside it")
			counter +=6

			image_writer = StripeImageWriter( width, height)

			"""
		# CYCL *****************************************************************
		# TODO: implement this Color cycling extraction functionality
		#       leaving this comment her for later imrpovements
		elif block_name == "CYCL":
			#cycles  : variable length
			#	idx   : 8 (valid range is [1-16])
			#	unk   : 16 Th
			#	freq  : 16be (delay = 16384/freq)
			#	flags : 16be
			#	start : 8 (start/end entries in the palette)
			#	end   : 8
			#close   : 8 must be set to 0 to end the block

			byte = file.read(1)
			print( byte )
			counter +=1

			while byte != b'\x00':
				cycle = {}

				cycle["idx"] = int.from_bytes( byte, byteorder='little', signed=False)

				byte = file.read(2)
				cycle["unk"] = int.from_bytes( byte, byteorder='little', signed=False)

				byte = file.read(2)
				cycle["freq"] = int.from_bytes( byte, byteorder='big', signed=False)

				byte = file.read(2)
				cycle["flags"] = int.from_bytes( byte, byteorder='big', signed=False)

				byte = file.read(1)
				cycle["start"] = int.from_bytes( byte, byteorder='little', signed=False)

				byte = file.read(1)
				cycle["end"] = int.from_bytes( byte, byteorder='little', signed=False)

				room_cycles.append( cycle )
				print( cycle )

				byte = file.read(1)
				counter += 9

			print(f"this is the end of the CYCL block")

			for c in room_cycles:
				#for k,v in c:
				#	print(f"cycle {k} --> {v}")
				print(c)
		"""

		# TRNS *****************************************************************
		# TRNS stores the transparency information of a room, namely, the palette
		# index to be treated as transparent.

		# "TRNS"	dword	Block identifier
		# dwSize	dword	Size in bytes (BE)
		# wIndex	word	Transparent palette index (LE)

		elif block_name == "TRNS":
			trasparent_index = file.read(2)
			trasparent_index = int.from_bytes( trasparent_index, byteorder='little', signed=False)
			print(f"this the transparent palette index color: {trasparent_index}")
			counter += 2


		# COLOR LOOK UP TABLE **************************************************
		elif block_name == "CLUT":
			print(f"CLUT: this the (VGA) color lookup table")

			for i in range(256):
				r = file.read(1)
				g = file.read(1)
				b = file.read(1)
				r = int.from_bytes( r, byteorder='little', signed=False)
				g = int.from_bytes( g, byteorder='little', signed=False)
				b = int.from_bytes( b, byteorder='little', signed=False)
				COLOR_LOOKUP_TABLE.append( (r,g,b) )

				#print(f"color {i}: [{r},{g},{b}]")
				counter +=3

			if SAVE_PALLETES:
				filename = os.path.join(current_dir, f"{PALETTE_FOLDER}/room{room_number}_off{room_abs_offset}.png")
				# filename, COLOR_LIST, width, height, scale_factor
				drawCLUT( filename, COLOR_LOOKUP_TABLE, 16,16, PALETTE_IMAGE_SCALE_FACTOR )

		# Actual background image data and z-planes ****************************
		elif block_name == "RMIM":

			# RMIH *************************************************************
			# only stores the number of z-planes for the background image
			block_name, block_size = readBlockHeader(file)
			assert block_name == "RMIH"
			counter += 8

			num_z_planes = file.read(2)
			num_z_planes = int.from_bytes( num_z_planes, byteorder='little', signed=False)
			print(f"number of z-planes (guessed) is : {num_z_planes}")
			counter += 2

			# IM00 *************************************************************
			block_name, block_size = readBlockHeader(file)
			assert block_name == "IM00"
			counter += 8


			# SMAP *************************************************************
			#ref: https://wiki.scummvm.org/index.php?title=SCUMM/Technical_Reference/Image_resources
			#ref: https://web.archive.org/web/20090727144325/http://scumm.mixnmojo.com/?page=articles/article1


			# What's in a Strip?
			# OK, so we find the strip offsets, we follow them one by one, but what
			# do we do when we get to a strip? OK, here's the information on what
			# is actually stored in the strip definitions.

			# The first byte in the strip data is the compression ID. This is a
			# number between 1 and 128 (0x80). We'll get to that in a second.
			# The next byte is the color of the first pixel in the strip, and also
			# the initial palette index. I.e., the palette index we continue
			# drawing with until we're told otherwise. After these two bytes
			# follow the actual compressed data.

			SMAP_REF_POSITION = file.tell()

			block_name, block_size = readBlockHeader(file)
			assert block_name == "SMAP"
			#counter += 8

			# first we will find the offset table
			num_stripes = int(width/8)
			print(f"Image width is '{width}' so we will have {num_stripes} stripes offsets")

			stripe_offsets = []
			for i in range(num_stripes):
				offset = file.read(4)
				offset = int.from_bytes( offset, byteorder='little', signed=False)
				#counter +=4
				stripe_offsets.append( offset )

			print( stripe_offsets )

			#try to rewind the file pointer
			#file.seek( -((4*num_stripes)+8), 1)  # 1 is `io.SEEK_CUR`
			#counter -= ((4*num_stripes)+8)
			file.seek( SMAP_REF_POSITION, 0)


			for i, so in enumerate(stripe_offsets):
				#move pointer to offset
				print(f"\nDrawing strip {i}, move forward by {so}")
				file.seek( so, 1 )

				# starting value for each strip for subtraction_variable is 1
				subtraction_var = 1

				compression_id = file.read(1)
				compression_id = int.from_bytes(compression_id, byteorder='little', signed=False)
				assert compression_id >= 1 and compression_id <= 128
				print(f"compression id of strip {i} is {compression_id} ({intToHex(compression_id)})")

				method, direction, transparent, parSub = getDecoderSettings( compression_id )
				palette_index_size = compression_id - parSub
				print(f"\ncodec info - compression ID: {intToHex(compression_id)}, method: {method}, direction: {direction}, tranparent: {transparent}, par-sub: {parSub}, so palette index size is {palette_index_size} bits\n")

				first_pixel_color_index = file.read(1)
				first_pixel_color_index = int.from_bytes(first_pixel_color_index, byteorder='little', signed=False)
				assert first_pixel_color_index <= 255
				print(f"first_pixel_color_index is {first_pixel_color_index}")

				# create an instance of the BitReader
				bitReader = BitReaderLSB( file )

				#remaining pixels to draw to the image
				pixel_left = 8 * height
				print(f"remaining {pixel_left} pixels to draw w/ {direction} method")

				color_index = first_pixel_color_index

				# Write the first pixel (always on the upper left corner)
				image_writer.write_pixel( i, COLOR_LOOKUP_TABLE[ color_index ], 1, direction )
				pixel_left -= 1

				if method == "1st":
					print(f"CODEC METHOD 1")

					# The elegant implementation for this decoder can be found here
					# ref: https://wiki.scummvm.org/index.php?title=SCUMM/Technical_Reference/Image_resources
					# This is known as 'UnkB'

					#uint8_t color = read_bits(csh);
					#uint8_t inc = -1;
					#while(pixel_left) {
					#  write_pixel(color,1);
					#  if(read_bit()) {
					#    if(!read_bit()) {
					#      color = read_bits(csh);
					#      inc = -1;
					#    } else {
					#      if(read_bit()) inc = -inc;
					#      color += inc;
					#    }
					#  }
					#}

					inc = -1

					while pixel_left > 0:


						if bitReader.read_bit():
							if not bitReader.read_bit():
								color_index = bitReader.read_bits( palette_index_size )
								inc = -1
							else:
								if bitReader.read_bit():
									inc = -inc
								color_index += inc

						image_writer.write_pixel( i, COLOR_LOOKUP_TABLE[ color_index ], 1, direction )
						pixel_left -= 1

					"""
					# Below is a more cluncky implementation of mine
					while pixel_left > 0:
						n = 1  # Default number of pixels to write
						if bitReader.read_bit():
							print("bit is one - looking for next code")
							#There are three codes that start in a 1
							#so we need the next bit to find out more


							if not bitReader.read_bit():
								print("found code 10 - read a new palette index")
								# bit is 0 so we have just encoutered the code '10'
								# code 10, which means we should read a new palette index
								# The code 10 also tells us to set the subtraction variable to 1 (it already is 1, as that's its initial value)
								color_index = bitReader.read_bits( palette_index_size )
								print( f"color index is {color_index}")
								assert color_index <= 255
								#if not color_index <=255:
								#	print(f"\nERROR: codec info - compression ID: {intToHex(compression_id)}, method: {method}, direction: {direction}, tranparent: {transparent}, par-sub: {parSub}, so palette index size is {palette_index_size} bits\n")
								#	color_index = 0
								subtraction_var = 1
								print(f"setting subtraction var to {subtraction_var}")
								# draw next pixel
								image_writer.write_pixel( i, COLOR_LOOKUP_TABLE[ color_index ], n, direction )
							else:
								#second bit is also 1: we have two different cases here
								if not bitReader.read_bit():
									print("found code 110")
									# we have encountered the code '110'
									#  110: Subtract the subtraction variable from the palette index, and draw the next pixel.
									color_index -= subtraction_var
									print( f"new color index is {color_index}")
									assert color_index <= 255
									#if not color_index <=255:
									#	print(f"\nERROR: codec info - compression ID: {intToHex(compression_id)}, method: {method}, direction: {direction}, tranparent: {transparent}, par-sub: {parSub}, so palette index size is {palette_index_size} bits\n")
									#	color_index = 0
									image_writer.write_pixel( i, COLOR_LOOKUP_TABLE[ color_index ], n, direction )
								else:
									print("found code 111 - negate subtraction var")
									# we have encountered the code '111'
									# 111: Negate the subtraction variable (i.e., if it's 1, change it to -1, if it's -1, change it to 1). Subtract it from the palette index, and draw the next pixel.
									subtraction_var = (-1)*subtraction_var
									print(f"negate the subtraction var which now is {subtraction_var}")
									color_index -= subtraction_var
									print( f"new color index is {color_index}")
									assert color_index <= 255
									#if not color_index <=255:
									#	print(f"\nERROR: codec info - compression ID: {intToHex(compression_id)}, method: {method}, direction: {direction}, tranparent: {transparent}, par-sub: {parSub}, so palette index size is {palette_index_size} bits\n")
									#	color_index = 0
									image_writer.write_pixel( i, COLOR_LOOKUP_TABLE[ color_index ], n, direction )
						else:
							#print("bit is zero - drawing a pixel")
							image_writer.write_pixel( i, COLOR_LOOKUP_TABLE[ color_index ], n, direction )

						pixel_left -= 1
					"""
				elif method == "2nd":
					print(f"CODEC METHOD 2")
					# as described here: https://web.archive.org/web/20090727144325/http://scumm.mixnmojo.com/?page=articles/article1
					# 0:  Draw next pixel with current palette index.
					# 10: Read a new palette index from the bitstream (i.e., the
					#     number of bits specified by the parameter), and draw the next pixel.
					# 11: Read the next 3 bit value, and perform an action, depending on the value:
					#     000 (0): Increase current palette index by 4.
					#     001 (1): Increase current palette index by 3.
					#     010 (2): Increase current palette index by 2.
					#     011 (3): Increase current palette index by 1.
					#     100 (4): Read next 8 bits. Draw the number of pixels
					#              specified by these 8 bits with the current palette
					#              index (somewhat similar to RLE).
					#     101 (5): Decrease current palette index by 1.
					#     110 (6): Decrease current palette index by 2.
					#     111 (7): Decrease current palette index by 3.

					# This seem a method to decode which is the one described as UnkA @
					# ref: https://wiki.scummvm.org/index.php?title=SCUMM/Technical_Reference/Image_resources
					# Trying this algo because the ine described here:
					# ref: https://web.archive.org/web/20090727144325/http://scumm.mixnmojo.com/?page=articles/article1
					# seems not to work

					while pixel_left > 0:
						n = 1
						if bitReader.read_bit():
							if not bitReader.read_bit():
								color_index = bitReader.read_bits( palette_index_size )
							else:
								inc = (bitReader.read_bits(3) - 4)
								if inc:
									color_index += inc
								else:
									n = bitReader.read_bits( 8 )
						if SAVE_BACKGROUND_IMAGE:
							image_writer.write_pixel( i, COLOR_LOOKUP_TABLE[ color_index ], n, direction )
						pixel_left -= 1

				file.seek( SMAP_REF_POSITION, 0)
				image_writer.moveToNextStrip( )


			if SAVE_BACKGROUND_IMAGE:
				# TODO: save image as bitmap image (with color palette inside)
				filename = os.path.join(current_dir, f"{BACKGROUND_IMAGES_FOLDER}/room{room_number}_off{room_abs_offset}.png")
				image_writer.save( filename, BACKGROUND_IMAGE_SCALE_FACTOR)

			# now, we are at the beginning of the SMAP block,
			# we have already processed it, so skip it
			file.seek( block_size, 1)
			counter += block_size

			"""
			block_name, block_size = readBlockHeader(file)
			assert block_name == "SMAP"
			counter += 8

			#skip actual sub-block data
			for i in range(block_size-8):
				byte = file.read(1)
				#print( byte )
				counter += 1
			"""

			# ZP0n *************************************************************
			print(f"Room has {num_z_planes} num z-planes")
			for i in range(num_z_planes):
				block_name, block_size = readBlockHeader(file)
				counter += 8

				assert block_name == f"ZP0{i+1}"
				#skip actual sub-block data
				for i in range(block_size-8):
					file.read(1)
					counter += 1

		else:
			#skip actual sub-block data
			for i in range(block_size-8):
				file.read(1)
				counter += 1

	return size


def readLFLF( file, room_number, current_dir ):
	SOUN_IDX = 0 #every lflf may have zero or more SOUN block, we use this counter to keep track of them
	COST_IDX = 0
	SCRP_IDX = 0
	CHAR_IDX = 0
	counter = 0

	abs_offset = file.tell()

	print( f"LFLF abs offset {abs_offset}\t(room number {room_number})" )

	_, lflf_block_size = readBlockHeader(file)
	counter += 8

	# ROOM
	# The ROOM block is the container for everything that makes up the appearance
	# and code (which was moved to the RMSC block in CMI, though) of a room
	# "ROOM" (dword) Block identifier
	# dwSize (dword) Size in bytes (BE)
	# followed by sub-blocks (the order and amount varies from game to game):
	# RMHD, CYCL, PALS, TRNS, EPAL, BOXD, BOXM, CLUT, SCAL, RMIM / IMAG, OBCD, EXCD, ENCD, NLSC, LSCR

	_, room_block_size = readBlockHeader(file)
	counter += 8

	# for now, skip all this content.
	# I think block size takes into account also:
	# * the 4 bytes for the block name;
	# * the 4 bytes for the block size itself;
	# so removing it because we already have traversed them

	size = readRoomData(file, room_block_size, room_number, abs_offset, current_dir)
	print(f"Size read is {size}")
	assert size == room_block_size
	counter += room_block_size

	#do we have more bytes to read?
	print(f"remaining {lflf_block_size - counter} bytes to be read - skipping")

	# now we can expect different type of sub blocks
	# like: SRC, SOUN, AKOS / COST, CHAR, SCRP
	while counter < lflf_block_size:
		absolute_offset = file.tell()
		#print()
		block_name, block_size = readBlockHeader(file) #SOUN, SCRP, COST, etc...
		counter += 8
		#print(f"remaining {lflf_block_size - counter} bytes to be read")

		if block_name == "SOUN":
			#print( f"SOUN abs offset: {absolute_offset}" )
			# ref: https://wiki.scummvm.org/index.php?title=SCUMM/Technical_Reference/Sound_resources
			# Going from Monkey Island 2 (MI2), music blocks are stored in LFLF blocks,
			# outside of the ROOMs, so they can be accessed globally. The containing sound block looks like this:
			# Block name         4 bytes ("SOUN")
			# Block size         4 bytes
			# Block name         4 bytes ("SOU ")
			# Block size         4 bytes
			# Music block        variable

			# "SOU "
			sou_block_name, sou_block_size = readBlockHeader(file)
			counter += 8
			#print(f"remaining {lflf_block_size - counter} bytes to be read")

			# The music block may contain any combination of ROL (Roland MT-32), ADL (AdLib/OPL FM),
			# or SPK (PC speaker) blocks. They can also store a single SBL block for digitized sound
			# (described in a later section). Aside from SBL, each of these blocks follow the same basic pattern.
			# Block name        4 bytes ("ROL ", or "ADL ", or "SPK ")
			# Block size        4 bytes
			# MIDI data         variable


			sou_counter = 0
			while sou_counter <= sou_block_size-8:
				# It seems to me that this block doesn't consider the 8 bytes of Block Name and Block Size
				sub_block_name, sub_block_size = readBlockHeader(file)
				#print(f"{sub_block_name} - size {sub_block_size}")

				file.seek(-8, 1) # rewind file pointer 8 bytes back from current position

				data_to_be_saved_as_MIDI = file.read( sub_block_size + 4 + 4 )

				sou_counter += (sub_block_size+8)
				#print(f"counter {counter} against parent block size {block_size}")
			SOUN_IDX += 1
			#print( "end of SOUN")

			counter = counter + sou_block_size
			#print(f"remaining {lflf_block_size - counter} bytes to be read")

		elif block_name == "COST":
			#print(f"This is a COST resource - size {block_size}, skipping")
			#skip this resource for now
			file.read(block_size-8)
			counter += block_size

		elif block_name == "SCRP":
			#print(f"This is a SCRP resource - size {block_size}, skipping")
			#skip this resource for now
			file.read(block_size-8)
			counter += block_size

		elif block_name == "CHAR":
			#print(f"This is a CHAR resource - size {block_size}, skipping")
			#skip this resource for now
			file.read(block_size-8)
			counter += block_size

		else:
			print("readLFLF method: pass")
			pass
		#print(f"counter {counter} against lflf block size {lflf_block_size}")

	print("end of LFLF block\n")


# MAIN #########################################################################
if __name__ == "__main__":
	# Get the absolute path of the current directory
	current_dir = os.getcwd() # Get the current working directory

	# I'm actually storing my game files in the parent folder
	os.chdir("..")
	parent_dir = os.getcwd() # Get the current working directory
	FILE_001 = os.path.join(parent_dir, FILE_001)  # Construct the full path

	file = BytesIO( xor( FILE_001 ) )
	reference_position = file.tell()
	print(f"ref pos: {reference_position}")

	# info taken from internal documentation of ScummEX software:

	# LECF block
	# description: LucasArts Entertainement Company
	#The LECF block is the root block of the main resource in all games from MI2 and on.
	# "LECF" (dword) block identifier
	# dwSize (dword) Size in bytes (BE)
	# blLOFF
	# loop
	#	* blLFLF
	# end of loop
	_, lecf_size = readBlockHeader(file)

	# LOFF block
	# The LOFF block contains the offsets to each LFLF block in the file
	# "LOFF" (dword) Block identifier
	# dwSize (dword) Size in bytes (BE)
	# nRooms (byte) Number of LFLF offsets
	# loop nRooms
	#	* nRoomNumber (byte) Room Number
	#	* dwOffset (dword) LFLF offset (LE)
	# enf of loop
	room_number_and_offset = []
	try:
		_, loff_size = readBlockHeader(file)
		nRoomsOffsets_byte = file.read(1)
		nRoomsOffsets = int.from_bytes(nRoomsOffsets_byte, 'little')
		print(f"total number of rooms: {nRoomsOffsets}")

		for room in range(nRoomsOffsets):
			roomNumber_byte = file.read(1)
			roomNumber = int.from_bytes(roomNumber_byte, 'little')
			offset_bytes = file.read(4)
			offset = int.from_bytes(offset_bytes, 'little')
			room_number_and_offset.append( [roomNumber, offset] )

	except Exception as e:
		print(f"Error: {e}")

	# rewind pointer to the start of the file
	file.seek(0)

	# do that for all the rooms
	for ro in room_number_and_offset :
		ROOM_NUMBER     = ro[0]
		ROOM_AB_OFFSET  = ro[1]
		LFLF_ABS_OFFSET = ROOM_AB_OFFSET - 8
		current_offset = file.tell()

		# move file pointer to the correct location in file
		file.seek( LFLF_ABS_OFFSET, 0)
		print( file.tell() )

		readLFLF( file, ROOM_NUMBER, current_dir)

		# rewind file pointer
		file.seek(0)
