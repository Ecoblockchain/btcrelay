# Stored variables:
#
# Last known block
# 10: version
# 11: hashPrevBlock
# 12: hashMerkleRoot
# 13: time
# 14: bits
# 15: nonce
# 16: blockHash / heaviestBlock
# 17: score
#

# block with the highest score (the end of the blockchain)
data heaviestBlock

# highest score among all blocks (so far)
data highScore

data block[2^256](_height, _score, _blockHeader(_version, _prevBlock, _mrklRoot, _time, _bits, _nonce))

extern btc_eth: [processTransfer]


#self.block.blockHeader[]

def shared():
    DIFFICULTY_1 = 0x00000000FFFF0000000000000000000000000000000000000000000000000000
    TWO_POW_24 = 2 ^ 24
    ZEROS = 0x0000000000000000000000000000000000000000000000000000000000000000
    LEFT_HASH = 1
    RIGHT_HASH = 2

def init():
    self.init333k()

def code():
    ret = self.shiftLeft(2,4)
    return(ret)




def storeBlockHeader(version, hashPrevBlock, hashMerkleRoot, time, bits, nonce):
    # this check can be removed to allow older block headers to be added, but it
    # may provide an attack vector where the contract can be spammed with valid
    # headers that will not be used and simply take up memory storage
    if hashPrevBlock != self.heaviestBlock:  # special case for genesis prev block of 0 is not needed since self.heaviestBlock is 0 initially
        return(0)

    blockHash = self.hashHeader(version, hashPrevBlock, hashMerkleRoot, time, bits, nonce)
    target = self.targetFromBits(bits)

    log(target)

    difficulty = DIFFICULTY_1 / target # https://en.bitcoin.it/wiki/Difficulty

    # TODO other validation of block?  eg timestamp

    if gt(blockHash, 0) && lt(blockHash, target):
        self.block[blockHash]._blockHeader._version = version
        self.block[blockHash]._blockHeader._prevBlock = hashPrevBlock
        self.block[blockHash]._blockHeader._mrklRoot = hashMerkleRoot
        self.block[blockHash]._blockHeader._time = time
        self.block[blockHash]._blockHeader._bits = bits
        self.block[blockHash]._blockHeader._nonce = nonce

        self.block[blockHash]._score = self.block[hashPrevBlock]._score + difficulty


        self.block[blockHash]._height = self.block[hashPrevBlock]._height + 1

        if gt(self.block[blockHash]._score, highScore):
            self.heaviestBlock = blockHash
            highScore = self.block[blockHash]._score

        return(self.block[blockHash]._height)

    return(0)



def flipBytes(n, numByte):
    mask = 0xff

    result = 0
    i = 0
    while i < numByte:
        b = n & mask
        b = div(b, 2^(i*8))
        b *= 2^((numByte-i-1)*8)
        mask *= 256
        result = result | b
        i += 1

    return(result)

# shift left
def shiftLeft(n, x):
    return(n * 2^x)

# shift right
def shiftRight(n, x):
    return(div(n, 2^x))

# pad with trailing zeros
#def rpad(val, numZero):


def test():
    # BTC_ETH = create('btc-eth.py')
    # res = BTC_ETH.processTransfer(13, as=btc_eth)
    res = self.testRelayTx()
    return(res)


def runTests():
    ALL_GOOD = 99999
    i = 100
    if self.testIsNonceValid() != 1:
        return(i)
    i += 1

    if self.test__rawHashBlockHeader() != 1:
        return(i)
    i += 1

    if self.testHashHeader() != 1:
        return(i)
    i += 1

    if self.testStoreBlockHeader() != 1:
        return(i)
    i += 1

    if self.testConcatHash() != 1:
        return(i)
    i += 1

    if self.testWithin6Confirms() != 1:
        return(i)
    i += 1

    if self.testComputeMerkle() != 1:
        return(i)
    i += 1

    if self.testVerifyTx() != 1:
        return(i)
    i += 1

    return(ALL_GOOD)

def isNonceValid(version, hashPrevBlock, hashMerkleRoot, time, bits, nonce):
    target = self.targetFromBits(bits)

    hash = self.hashHeader(version, hashPrevBlock, hashMerkleRoot, time, bits, nonce)

    if lt(hash, target):
        return(1)
    else:
        return(0)


def targetFromBits(bits):
    exp = div(bits, TWO_POW_24)
    mant = bits & 0xffffff
    target = mant * self.shiftLeft(1, (8*(exp - 3)))
    return(target)

# http://www.righto.com/2014/02/bitcoin-mining-hard-way-algorithms.html#ref3
def testTargetFromBits():
    bits = 0x19015f53
    exp = 8614444778121073626993210829679478604092861119379437256704
    res = self.targetFromBits(bits)
    return(res == exp)


def hashHeader(version, hashPrevBlock, hashMerkleRoot, time, bits, nonce):
    version = self.flipBytes(version, 4)
    hashPrevBlock = self.flipBytes(hashPrevBlock, 32)
    hashMerkleRoot = self.flipBytes(hashMerkleRoot, 32)
    time = self.flipBytes(time, 4)
    bits = self.flipBytes(bits, 4)
    nonce = self.flipBytes(nonce, 4)

    hash = self.__rawHashBlockHeader(version, hashPrevBlock, hashMerkleRoot, time, bits, nonce)
    return(self.flipBytes(hash, 32))

def __rawHashBlockHeader(version, hashPrevBlock, hashMerkleRoot, time, bits, nonce):
    verPart = self.shiftLeft(version, 28*8)
    hpb28 = self.shiftRight(hashPrevBlock, 4*8)  # 81cd02ab7e569e8bcd9317e2fe99f2de44d49ab2b8851ba4a3080000
    b1 = verPart | hpb28

    hpbLast4 = self.shiftLeft(hashPrevBlock, 28*8)  # 000000000
    hm28 = self.shiftRight(hashMerkleRoot, 4*8)  # e320b6c2fffc8d750423db8b1eb942ae710e951ed797f7affc8892b0
    b2 = hpbLast4 | hm28

    hmLast4 = self.shiftLeft(hashMerkleRoot, 28*8)
    timePart = ZEROS | self.shiftLeft(time, 24*8)
    bitsPart = ZEROS | self.shiftLeft(bits, 20*8)
    noncePart = ZEROS | self.shiftLeft(nonce, 16*8)
    b3 = hmLast4 | timePart | bitsPart | noncePart

    hash1 = sha256([b1,b2,b3], chars=80)
    hash2 = sha256([hash1], items=1)
    return(hash2)


def verifyTx(tx, proofLen, hash:arr, path:arr, txBlockHash):
    if self.within6Confirms(txBlockHash):
        return(0)

    merkle = self.computeMerkle(tx, proofLen, hash, path)

    if merkle == self.block[txBlockHash]._blockHeader._mrklRoot:
        return(1)
    else:
        return(0)

def relayTx(tx, proofLen, hash:arr, path:arr, txBlockHash, contract):
    if self.verifyTx(tx, proofLen, hash, path, txBlockHash) == 1:
        res = contract.processTransfer(13, as=btc_eth)
        return(res)
        # return(call(contract, tx))
    return(0)

def testRelayTx():
    # this is duped from testVerifyTx since there seems to be issues with accessing arrays
    # returned by a function (see setupProof branch)

    b0 = 0x000000000003ba27aa200b1cecaad478d2b00432346c3f1f3986da1afd33e506
    b1 = 0x00000000000080b66c911bd5ba14a74260057311eaeb1982802f7010f1a9f090 # block #100001
    b2 = 0x0000000000013b8ab2cd513b0261a14096412195a72a0c4827d229dcc7e0f7af
    b3 = 0x000000000002a0a74129007b1481d498d0ff29725e9f403837d517683abac5e1
    b4 = 0x000000000000b0b8b4e8105d62300d63c8ec1a1df0af1c2cdbd943b156a8cd79
    b5 = 0x000000000000dab0130bbcc991d3d7ae6b81aa6f50a798888dfe62337458dc45
    b6 = 0x0000000000009b958a82c10804bd667722799cc3b457bc061cd4b7779110cd60

    self.heaviestBlock = b6

    self.block[b6]._blockHeader._prevBlock = b5
    self.block[b5]._blockHeader._prevBlock = b4
    self.block[b4]._blockHeader._prevBlock = b3
    self.block[b3]._blockHeader._prevBlock = b2
    self.block[b2]._blockHeader._prevBlock = b1
    self.block[b1]._blockHeader._prevBlock = b0

    self.block[b0]._blockHeader._mrklRoot = 0xf3e94742aca4b5ef85488dc37c06c3282295ffec960994b2c0d5ac2a25a95766

    # values are from block 100K
    tx = 0x8c14f0db3df150123e6f3dbbf30f8b955a8249b62ac1d1ff16284aefa3d06d87
    proofLen = 2
    hash = array(proofLen)
    path = array(proofLen)

    hash[0] = 0xfff2525b8931402dd09222c50775608f75787bd2b87e56995a7bdd30f79702c4
    path[0] = RIGHT_HASH

    hash[1] = 0x8e30899078ca1813be036a073bbf80b86cdddde1c96e9e9c99e9e3782df4ae49
    path[1] = RIGHT_HASH

    txBlockHash = b0
    BTC_ETH = create('btc-eth.py')
    res = self.relayTx(tx, proofLen, hash, path, txBlockHash, BTC_ETH)
    return(res)
    # expB0 = 1 == self.relayTx(tx, proofLen, hash, path, txBlockHash)
    # return(-1)

def testVerifyTx():
    # verifyTx should only return 1 for b0
    b0 = 0x000000000003ba27aa200b1cecaad478d2b00432346c3f1f3986da1afd33e506
    b1 = 0x00000000000080b66c911bd5ba14a74260057311eaeb1982802f7010f1a9f090 # block #100001
    b2 = 0x0000000000013b8ab2cd513b0261a14096412195a72a0c4827d229dcc7e0f7af
    b3 = 0x000000000002a0a74129007b1481d498d0ff29725e9f403837d517683abac5e1
    b4 = 0x000000000000b0b8b4e8105d62300d63c8ec1a1df0af1c2cdbd943b156a8cd79
    b5 = 0x000000000000dab0130bbcc991d3d7ae6b81aa6f50a798888dfe62337458dc45
    b6 = 0x0000000000009b958a82c10804bd667722799cc3b457bc061cd4b7779110cd60

    self.heaviestBlock = b6

    self.block[b6]._blockHeader._prevBlock = b5
    self.block[b5]._blockHeader._prevBlock = b4
    self.block[b4]._blockHeader._prevBlock = b3
    self.block[b3]._blockHeader._prevBlock = b2
    self.block[b2]._blockHeader._prevBlock = b1
    self.block[b1]._blockHeader._prevBlock = b0

    self.block[b0]._blockHeader._mrklRoot = 0xf3e94742aca4b5ef85488dc37c06c3282295ffec960994b2c0d5ac2a25a95766

    # values are from block 100K
    tx = 0x8c14f0db3df150123e6f3dbbf30f8b955a8249b62ac1d1ff16284aefa3d06d87
    proofLen = 2
    hash = array(proofLen)
    path = array(proofLen)

    hash[0] = 0xfff2525b8931402dd09222c50775608f75787bd2b87e56995a7bdd30f79702c4
    path[0] = RIGHT_HASH

    hash[1] = 0x8e30899078ca1813be036a073bbf80b86cdddde1c96e9e9c99e9e3782df4ae49
    path[1] = RIGHT_HASH

    txBlockHash = 0xdead
    expFake = 0 == self.verifyTx(tx, proofLen, hash, path, txBlockHash)

    txBlockHash = b1
    expB1 = 0 == self.verifyTx(tx, proofLen, hash, path, txBlockHash)

    # verifyTx should only return 1 for b0
    txBlockHash = b0
    expB0 = 1 == self.verifyTx(tx, proofLen, hash, path, txBlockHash)

    return(expFake and expB1 and expB0)


# return -1 if there's an error (eg called with incorrect params)
def computeMerkle(tx, proofLen, hash:arr, path:arr):
    resultHash = tx
    i = 0
    while i < proofLen:
        proofHex = hash[i]
        if path[i] == LEFT_HASH:
            left = proofHex
            right = resultHash
        elif path[i] == RIGHT_HASH:
            left = resultHash
            right = proofHex

        resultHash = self.concatHash(left, right)

        i += 1

    if !resultHash:
        return(-1)

    return(resultHash)

def testComputeMerkle():
    # values are from block 100K
    tx = 0x8c14f0db3df150123e6f3dbbf30f8b955a8249b62ac1d1ff16284aefa3d06d87
    proofLen = 2
    hash = array(proofLen)
    path = array(proofLen)

    hash[0] = 0xfff2525b8931402dd09222c50775608f75787bd2b87e56995a7bdd30f79702c4
    path[0] = RIGHT_HASH

    hash[1] = 0x8e30899078ca1813be036a073bbf80b86cdddde1c96e9e9c99e9e3782df4ae49
    path[1] = RIGHT_HASH

    r = self.computeMerkle(tx, proofLen, hash, path)
    expMerkle = 0xf3e94742aca4b5ef85488dc37c06c3282295ffec960994b2c0d5ac2a25a95766
    return(r == expMerkle)

def within6Confirms(txBlockHash):
    blockHash = self.heaviestBlock

    i = 0
    while i < 6:
        if txBlockHash == blockHash:
            return(1)

        blockHash = self.block[blockHash]._blockHeader._prevBlock
        i += 1

    return(0)

def concatHash(tx1, tx2):
    left = self.flipBytes(tx1, 32)
    right = self.flipBytes(tx2, 32)

    hash1 = sha256([left, right], chars=64)
    hash2 = sha256([hash1], 1)

    return(self.flipBytes(hash2, 32))


def testWithin6Confirms():
    self.init333k()
    b0 = 0x000000000000000008360c20a2ceff91cc8c4f357932377f48659b37bb86c759
    b1 = 0x000000000000000010e318d0c61da0b84246481d9cc097fda9327fe90b1538c1 # block #333001
    b2 = 0x000000000000000005895c1348171a774e11ee57374680b54a982e9d9e7309a1
    b3 = 0x00000000000000001348f0e7b14d82d8105992f0968faeb533a03c55c3d72365
    b4 = 0x000000000000000004001d114c6c278eb0ad37a3ce3a111cf534dd358896c5b3
    b5 = 0x000000000000000004860a07b991a6cd7cae1327c36c21903b8bbe8d2c316ac5
    b6 = 0x0000000000000000016f889a84b7a06e2d4d90cec924400cf62a6ca3ae67dd46

    self.heaviestBlock = b6

    self.block[b6]._blockHeader._prevBlock = b5
    self.block[b5]._blockHeader._prevBlock = b4
    self.block[b4]._blockHeader._prevBlock = b3
    self.block[b3]._blockHeader._prevBlock = b2
    self.block[b2]._blockHeader._prevBlock = b1
    self.block[b1]._blockHeader._prevBlock = b0

    expB6 = self.within6Confirms(b6) == 1
    expB5 = self.within6Confirms(b5) == 1
    expB1 = self.within6Confirms(b1) == 1
    expB0 = self.within6Confirms(b0) == 0

    return(expB6 and expB5 and expB1 and expB0)

def testConcatHash():
    tx1 = 0x8c14f0db3df150123e6f3dbbf30f8b955a8249b62ac1d1ff16284aefa3d06d87
    tx2 = 0xfff2525b8931402dd09222c50775608f75787bd2b87e56995a7bdd30f79702c4
    r = self.concatHash(tx1, tx2)
    return(r == 0xccdafb73d8dcd0173d5d5c3c9a0770d0b3953db889dab99ef05b1907518cb815)


def testStoreBlockHeader():
    self.init333k()
    version = 2
    hashPrevBlock = 0x000000000000000008360c20a2ceff91cc8c4f357932377f48659b37bb86c759
    hashMerkleRoot = 0xf6f8bc90fd41f626705ac8de7efe7ac723ba02f6d00eab29c6fe36a757779ddd
    time = 1417792088
    bits = 0x181b7b74
    nonce = 796195988
    blockNumber = 333001

    return(blockNumber == self.storeBlockHeader(version, hashPrevBlock, hashMerkleRoot, time, bits, nonce))


def testHashHeader():
    version = 2
    hashPrevBlock = 0x000000000000000008360c20a2ceff91cc8c4f357932377f48659b37bb86c759
    hashMerkleRoot = 0xf6f8bc90fd41f626705ac8de7efe7ac723ba02f6d00eab29c6fe36a757779ddd
    time = 1417792088
    bits = 0x181b7b74
    nonce = 796195988

    expBlockHash = 0x000000000000000010e318d0c61da0b84246481d9cc097fda9327fe90b1538c1
    blockHash = self.hashHeader(version, hashPrevBlock, hashMerkleRoot, time, bits, nonce)
    return(blockHash == expBlockHash)


def test__rawHashBlockHeader():
    # https://en.bitcoin.it/wiki/Block_hashing_algorithm
    version = 0x01000000
    hashPrevBlock = 0x81cd02ab7e569e8bcd9317e2fe99f2de44d49ab2b8851ba4a308000000000000
    hashMerkleRoot = 0xe320b6c2fffc8d750423db8b1eb942ae710e951ed797f7affc8892b0f1fc122b
    time = 0xc7f5d74d
    bits = 0xf2b9441a
    nonce = 0x42a14695

    # these should be the intermediate b1,b2,b3 values inside __rawHashBlockHeader()
    # b1 = 0x0100000081cd02ab7e569e8bcd9317e2fe99f2de44d49ab2b8851ba4a3080000
    # b2 = 0x00000000e320b6c2fffc8d750423db8b1eb942ae710e951ed797f7affc8892b0
    # b3 = 0xf1fc122bc7f5d74df2b9441a42a1469500000000000000000000000000000000
    # hash1 = sha256([b1,b2,b3], chars=80)
    # hash2 = sha256([hash1], 1)
    # return(hash2)

    res = self.__rawHashBlockHeader(version, hashPrevBlock, hashMerkleRoot, time, bits, nonce)
    # log(res)

    expHash = 0x1dbd981fe6985776b644b173a4d0385ddc1aa2a829688d1e0000000000000000
    return res == expHash

def init333k():
    self.heaviestBlock = 0x000000000000000008360c20a2ceff91cc8c4f357932377f48659b37bb86c759
    trustedBlock = self.heaviestBlock
    self.block[trustedBlock]._height = 333000
    self.block[trustedBlock]._blockHeader._version = 2

def testIsNonceValid():
    ver = 2
    prev_block = 0x000000000000000117c80378b8da0e33559b5997f2ad55e2f7d18ec1975b9717
    mrkl_root = 0x871714dcbae6c8193a2bb9b2a69fe1c0440399f38d94b3a0f1b447275a29978a
    time_ = 0x53058b35 # 2014-02-20 04:57:25
    bits = 0x19015f53
    nonce = 856192328

    res = self.isNonceValid(ver, prev_block, mrkl_root, time_, bits, nonce)
    return(res)
