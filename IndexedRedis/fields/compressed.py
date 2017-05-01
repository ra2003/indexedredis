# Copyright (c) 2014, 2015, 2016, 2017 Timothy Savannah under LGPL version 2.1. See LICENSE for more information.
#
# fields.compressed - Some types and objects related to compressed fields. Use in place of IRField ( in FIELDS array to activate functionality )
#


# vim: set ts=8 shiftwidth=8 softtabstop=8 noexpandtab :


import zlib
import bz2

from . import IRField, irNull

from ..compat_str import tobytes, isEmptyString, getDefaultIREncoding, isStringy


__all__ = ('COMPRESS_MODE_BZ2', 'COMPRESS_MODE_ZLIB', 'IRCompressedField')

# COMPRESS_MODE_ZLIB - Use to compress using zlib (gzip)
COMPRESS_MODE_ZLIB = 'zlib'

# All aliases for gzip compression
_COMPRESS_MODE_ALIASES_ZLIB = ('gzip', 'gz')

# COMPRESS_MODE_BZ2 - Use to compress using bz2 (bz2)
COMPRESS_MODE_BZ2 = 'bz2'

_COMPRESS_MODE_ALIASES_BZ2 = ('bzip2', )


class IRCompressedField(IRField):
	'''
		IRCompressedField - A field that automatically compresses/decompresses going to/from Redis.

		Pass this into the FIELDS array of the model to get this functionality,

		like: 
			FIELDS  = [ ..., IRCompressedField('my_compressed_field', compressMode=COMPRESS_MODE_ZLIB]

		By default, after fetch the data will be encoded as "bytes". If you need it to be unicode/string, use an
		  IRFieldChain with an IRUnicodeField and an IRCompressedField together.

		An IRCompressedField is indexable, and forces the index to be hashed.
	'''

	CAN_INDEX = True
	hashIndex = True

	# NOTE: We don't support different compression levels, as doing so changes header and would prevent indexing.
	def __init__(self, name='', compressMode=COMPRESS_MODE_ZLIB, defaultValue=irNull):
		'''
			__init__ - Create this object

			@param name <str> - Field name
			@param compressMode <str>, default "zlib". Determines the compression module to use
			  for this field. See COMPRESS_MODE_* variables in this module.

			  Supported values as of 5.0.0 are:

			     "zlib" / "gz" / "gzip" - zlib compression
			     "bz2"  / "bzip2"       - bzip2 compression
			
			@param defaultValue - The default value for this field

			An IRCompressedField is indexable, and forces the index to be hashed.
		'''
		self.valueType = None
		self.defaultValue = defaultValue

		if compressMode == COMPRESS_MODE_ZLIB or compressMode in _COMPRESS_MODE_ALIASES_ZLIB:
			self.compressMode = COMPRESS_MODE_ZLIB
			self.header = b'x\xda'
		elif compressMode == COMPRESS_MODE_BZ2 or compressMode in _COMPRESS_MODE_ALIASES_BZ2:
			self.compressMode = COMPRESS_MODE_BZ2
			self.header = b'BZh9'
		else:
			raise ValueError('Invalid compressMode, "%s", for field "%s". Should be one of the IndexedRedis.fields.compressed.COMPRESS_MODE_* constants.' %(str(compressMode), name))


	def getCompressMod(self):
		'''
			getCompressMod - Return the module used for compression on this field

			@return <module> - The module for compression
		'''
		if self.compressMode == COMPRESS_MODE_ZLIB:
			return zlib
		if self.compressMode == COMPRESS_MODE_BZ2:
			return bz2

	def _toStorage(self, value):
		if isEmptyString(value):
			return ''


		try:
			valueBytes = tobytes(value)
		except Exception as e:
			raise ValueError('Failed to convert value to bytes. If this requires a different codec than the defaultIREncoding (currently %s), use an IRFieldChain with an IRBytesField or IRUnicodeField with the required encoding set (Depending on if you want the uncompressed value to be "bytes" or "unicode" type). Exception was: <%s> %s' %(getDefaultIREncoding(), e.__class__.__name__, str(e)) )

		# TODO: I don't think this next block is needed anymore..
		#   Check it out when IRCompressionTest is written
		if tobytes(value[:len(self.header)]) == self.header:
			return value


		return self.getCompressMod().compress(tobytes(value), 9)

	def _fromStorage(self, value):

		if isEmptyString(value):
			return ''

		# TODO: Check this out too, this enxt conditional probably shouldn't be here, maybe it should be an error when false..
		if isStringy(value) and tobytes(value[:len(self.header)]) == self.header:
			return self.getCompressMod().decompress(value)

		return value
	
	def _fromInput(self, value):
		return value

	def _getReprProperties(self):
		return [ 'compressMode="%s"' %(self.compressMode, ) ]

	def copy(self):
		return self.__class__(name=self.name, compressMode=self.compressMode, defaultValue=self.defaultValue)

	def __new__(self, name='', compressMode=COMPRESS_MODE_ZLIB, defaultValue=irNull):
		return IRField.__new__(self, name)


# vim:set ts=8 shiftwidth=8 softtabstop=8 noexpandtab :
