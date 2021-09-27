from bitstring import BitArray


def addPadding(s, mod):
    if ((len(s) * 8) % mod):
        return s + " " * (8-((len(s) * 8) % mod)//8)
    else:
        return s

def tobits(s , capacity = 64):

    result = []
    for c in s:
        bits = bin(ord(c))[2:]
        bits = '00000000'[len(bits):] + bits
        result.extend([int(b) for b in bits])

    r = BitArray(capacity)
    for i in range(capacity+64):
        if i < len(result):
            r[i] = (result[i] == True)
    return r

def frombits(bitarray):
    chars = []
    bits = []
    for i in range(bitarray.len):
        bits.append(int(bitarray[i]))
    for b in range(len(bits) // 8):
        byte = bits[b*8:(b+1)*8]
        chars.append(chr(int(''.join([str(bit) for bit in byte]), 2)))
    return ''.join(chars)

class DES:

    def __init__(self):

        self._IP = [
            58, 50, 42, 34, 26, 18, 10, 2,
            60, 52, 44, 36, 28, 20, 12, 4,
            62, 54, 46, 38, 30, 22, 14, 6,
            64, 56, 48, 40, 32, 24, 16, 8,
            57, 49, 41, 33, 25, 17,  9, 1,
            59, 51, 43, 35, 27, 19, 11, 3,
            61, 53, 45, 37, 29, 21, 13, 5,
            63, 55, 47, 39, 31, 23, 15, 7
        ]

        self._PC1_L = [
            57, 49, 41, 33, 25, 17, 9 ,
            1 , 58, 50, 42, 34, 26, 18,
            10, 2 , 59, 51, 43, 35, 27,
            19, 11, 3 , 60, 52, 44, 36
        ]

        self._PC1_R = [
            63, 55, 47, 39, 31, 23, 15,
            7 , 62, 54, 46, 38, 30, 22,
            14, 6 , 61, 53, 45, 37, 29,
            21, 13,  5, 28, 20, 12,  4
        ]

        self._PC2 = [
            14, 17, 11, 24,  1,  5,
            3 , 28, 15,  6, 21, 10,
            23, 19, 12,  4, 26,  8,
            16,  7, 27, 20, 13,  2,
            41, 52, 31, 37, 47, 55,
            30, 40, 51, 45, 33, 48,
            44, 49, 39, 56, 34, 53,
            46, 42, 50, 36, 29, 32
        ]

        self._ROT_SCHED = [1,1,2,2,2,2,2,2,1,2,2,2,2,2,2,1]

        self._E = [
            32,  1,  2,  3,  4,  5,
             4,  5,  6,  7,  8,  9,
             8,  9, 10, 11, 12, 13,
            12, 13, 14, 15, 16, 17,
            16, 17, 18, 19, 20, 21,
            20, 21, 22, 23, 24, 25,
            24, 25, 26, 27, 28, 29,
            28, 29, 30, 31, 32,  1
        ]

    def encrypt(self, message, key):


        m_padded = addPadding(message, 64)
        bitM = tobits(m_padded, len(m_padded)*8)

        if not isinstance(key, BitArray):
            k_padded = addPadding(key, 64)
            bitK = tobits(k_padded, len(k_padded)*8)

        else:
            bitK = key

        keys = self._generateSubkeys(bitK)
        blocks = bitM.cut(64)
        enc = BitArray(0)

        for block in blocks:
            enc+=(self._encryptBlock(block, keys))

        return frombits(enc)

    def decrypt(self, message, key):

        bitM = tobits(message, len(message) * 8)

        if not isinstance(key, BitArray):
            k_padded = addPadding(key, 64)
            bitK = tobits(k_padded, len(k_padded)*8)

        else:
            bitK = key

        keys = self._generateSubkeys(bitK)

        blocks = bitM.cut(64)

        enc = BitArray(0)

        for block in blocks:
            enc += (self._decryptBlock(block, keys))

        return frombits(enc)

    def encryptFile(self, filepath, key=None, keypath=None):

        if key==None and keypath==None:
            raise Exception("No key supplied")

        with open(filepath, 'r') as f:

            s = f.read()
            si = self.encrypt()

    def _gen1erateSubkeys(self, key):

        K = []

        def init(key_in):
            Ci = BitArray(28)
            Di = BitArray(28)

            Ci.set(True, [i for i in range(28) if key_in[self._PC1_L[i]-1]])
            Di.set(True, [i for i in range(28) if key_in[self._PC1_R[i] - 1]])

            return Ci+Di

        def stage(key_in, i):
            Ci = BitArray(28)
            Di = BitArray(28)

            Ci, Di = key_in.cut(28)

            Ci.rol(self._ROT_SCHED[i])
            Di.rol(self._ROT_SCHED[i])

            PC2_in = Ci+Di

            Ki = BitArray(48)
            Ki.set(True, [i  for i in range(len(self._PC2)) if PC2_in[self._PC2[i]-1]])

            return Ki, PC2_in

        nextIn = init(key)
        for i in range(16):

            Ki, nextIn = stage(nextIn, i)
            K.append(Ki)

        return K

    def __IP(self, m):

        b = BitArray(64)
        b.set(True, [i for i in range(64) if m[self._IP[i]-1]])
        return b

    def __IIP(self, m):

        IIP = [40, 8, 48, 16, 56, 24, 64, 32, 39, 7, 47, 15, 55, 23, 63, 31, 38, 6, 46, 14, 54, 22, 62, 30, 37, 5, 45, 13, 53, 21, 61, 29, 36, 4, 44, 12, 52, 20, 60, 28, 35, 3, 43, 11, 51, 19, 59, 27, 34, 2, 42, 10, 50, 18, 58, 26, 33, 1, 41, 9, 49, 17, 57, 25]

        b= BitArray(64)
        b.set(True, [i for i in range(64) if m[IIP[i] - 1]])
        return b

    def __E(self, m):
        b = BitArray(48)
        b.set(True, [i for i in range(48) if m[self._E[i] - 1]])

        return b

    def __S(self, m):

        S1 = [
            [14,4,13,1,2,15,11,8,3,10,6,12,5,9,0,7],
            [0,15,7,4,14,2,13,1,10,6,12,11,9,5,3,8],
            [4,1,14,8,13,6,2,11,15,12,9,7,3,10,5,0],
            [15,12,8,2,4,9,1,7,5,11,3,14,10,0,6,13]
        ]

        S2 = [
            [15,1,8,14,6,11,3,4,9,7,2,13,12,0,5,10],
            [3,13,4,7,15,2,8,14,12,0,1,10,6,9,11,5],
            [0,14,7,11,10,4,13,1,5,8,12,6,9,3,2,15],
            [13,8,10,1,3,15,4,2,11,6,7,12,0,5,14,9]
        ]

        S3 = [
            [10, 0, 9, 14, 6, 3, 15, 5, 1, 13, 12, 7, 11, 4, 2, 8],
            [13, 7, 0, 9, 3, 4, 6, 10, 2, 8, 5, 14, 12, 11, 15, 1],
            [13, 6, 4, 9, 8, 15, 3, 0, 11, 1, 2, 12, 5, 10, 14, 7],
            [1, 10, 13, 0, 6, 9, 8, 7, 4, 15, 14, 3, 11, 5, 2, 12]
        ]

        S4 = [
            [7, 13, 14, 3, 0, 6, 9, 10, 1, 2, 8, 5, 11, 12, 4, 15],
            [13, 8, 11, 5, 6, 15, 0, 3, 4, 7, 2, 12, 1, 10, 14, 9],
            [10, 6, 9, 0, 12, 11, 7, 13, 15, 1, 3, 14, 5, 2, 8, 4],
            [3, 15, 0, 6, 10, 1, 13, 8, 9, 4, 5, 11, 12, 7, 2, 14]
        ]

        S5 = [
            [2, 12, 4, 1, 7, 10, 11, 6, 8, 5, 3, 15, 13, 0, 14, 9],
            [14, 11, 2, 12, 4, 7, 13, 1, 5, 0, 15, 10, 3, 9, 8, 6],
            [4, 2, 1, 11, 10, 13, 7, 8, 15, 9, 12, 5, 6, 3, 0, 14],
            [11, 8, 12, 7, 1, 14, 2, 13, 6, 15, 0, 9, 10, 4, 5, 3]
        ]

        S6 = [
            [12, 1, 10, 15, 9, 2, 6, 8, 0, 13, 3, 4, 14, 7, 5, 11],
            [10, 15, 4, 2, 7, 12, 9, 5, 6, 1, 13, 14, 0, 11, 3, 8],
            [9, 14, 15, 5, 2, 8, 12, 3, 7, 0, 4, 10, 1, 13, 11, 6],
            [4, 3, 2, 12, 9, 5, 15, 10, 11, 14, 1, 7, 6, 0, 8, 13]
        ]

        S7 = [
            [4, 11, 2, 14, 15, 0, 8, 13, 3, 12, 9, 7, 5, 10, 6, 1],
            [13, 0, 11, 7, 4, 9, 1, 10, 14, 3, 5, 12, 2, 15, 8, 6],
            [1, 4, 11, 13, 12, 3, 7, 14, 10, 15, 6, 8, 0, 5, 9, 2],
            [6, 11, 13, 8, 1, 4, 10, 7, 9, 5, 0, 15, 14, 2, 3, 12]
        ]

        S8 = [
            [13, 2, 8, 4, 6, 15, 11, 1, 10, 9, 3, 14, 5, 0, 12, 7],
            [1, 15, 13, 8, 10, 3, 7, 4, 12, 5, 6, 11, 0, 14, 9, 2],
            [7, 11, 4, 1, 9, 12, 14, 2, 0, 6, 10, 13, 15, 3, 5, 8],
            [2, 1, 14, 7, 4, 10, 8, 13, 15, 12, 9, 0, 3, 5, 6, 11]
        ]

        S = [S1,S2,S3,S4,S5,S6,S7,S8]

        out = BitArray(0)
        for i in range(8):

            s_in = m[6*i:(i+1)*6]

            row = BitArray(2)
            row[0] = s_in[0]
            row[1] = s_in[5]

            col = BitArray(4)
            col[:] = s_in[1:5]

            s_out = BitArray(4)
            s_out.uint = S[i][row.uint][col.uint]

            #print(f'S({s_in.bin}) = {s_out.uint}')

            out = out+s_out

        return out

    def __P(self, m):

        P = [16, 7, 20, 21, 29, 12, 28, 17, 1, 15, 23, 26, 5, 18, 31, 10, 2, 8, 24, 14, 32, 27, 3, 9, 19, 13, 30, 6, 22, 11, 4, 25]

        b = BitArray(32)
        b.set(True,[i for i in range(32) if m[P[i]-1]])

        return b

    def _encryptBlock(self, m, keys):

        Li, Ri= self.__IP(m).cut(32)

        def stage(Li, Ri, Ki):

            #print("Li", Li.bin)
            #print("Ri", Ri.bin)

            def F(R, K):

                ER = self.__E(R)
                #print("E(R)=",ER.bin)
                XOROUT = ER ^ K
                #print("A=E(R) XOR K=", XOROUT.bin)

                S_OUT = self.__S(XOROUT)
                #print("B=S(A)=", S_OUT.bin)
                P_OUT = self.__P(S_OUT)
                #print("P(B)=", P_OUT.bin)

                return P_OUT

            Rii = F(Ri, Ki) ^ Li
            Lii = Ri

            #print("Li+1=",Lii.bin)
            #print("Ri+1=", Rii.bin)

            return Lii, Rii

        for i in range(16):
            Li, Ri = stage(Li,Ri,keys[i])

        return self.__IIP(Ri+Li)

    def _decryptBlock(self, m, keys):

        return self._encryptBlock(m, keys[::-1])

