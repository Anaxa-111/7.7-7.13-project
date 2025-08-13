import struct

# 模拟 C++ 的 ROTL
def ROTL(x, n):
    n = n % 32
    return ((x << n) | (x >> (32 - n))) & 0xFFFFFFFF

# 定义 FF, GG, P0, P1
def FF(x, y, z, j):
    if j < 16:
        return x ^ y ^ z
    else:
        return (x & y) | (x & z) | (y & z)

def GG(x, y, z, j):
    if j < 16:
        return x ^ y ^ z
    else:
        return (x & y) | (~x & z) & 0xFFFFFFFF

def P0(x):
    return x ^ ROTL(x, 9) ^ ROTL(x, 17)

def P1(x):
    return x ^ ROTL(x, 15) ^ ROTL(x, 23)

# SM3 初始向量 (IV)
IV = [
    0x7380166f, 0x4914b2b9, 0x172442d7, 0xda8a0600,
    0xa96f30bc, 0x163138aa, 0xe38dee4d, 0xb0fb0e4e
]

# T_j 常量
T_j = [0x79cc4519] * 16 + [0x7a879d8a] * 48

# SM3 压缩函数
def sm3_compress(V, B):
    W = [0] * 68
    W1 = [0] * 64

    # 1. 将 512-bit 块 M 拆分为 16 个 32-bit 字 W0, W1, ..., W15
    for i in range(16):
        W[i] = struct.unpack(">I", B[i * 4 : i * 4 + 4])[0] # 大端序 unsigned int

    # 2. 扩展消息字
    for i in range(16, 68):
        W[i] = P1(W[i - 16] ^ W[i - 9] ^ ROTL(W[i - 3], 15)) ^ ROTL(W[i - 13], 7) ^ W[i - 6]
        W[i] = W[i] & 0xFFFFFFFF  # Ensure 32-bit

    # 3. 消息字扩展
    for i in range(64):
        W1[i] = W[i] ^ W[i + 4]
        W1[i] = W1[i] & 0xFFFFFFFF  # Ensure 32-bit

    # 4. 压缩函数
    A, B_, C, D = V[0], V[1], V[2], V[3]
    E, F, G, H = V[4], V[5], V[6], V[7]

    for j in range(64):
        SS1 = ROTL((ROTL(A, 12) + E + ROTL(T_j[j], j % 32)), 7) & 0xFFFFFFFF
        SS2 = SS1 ^ ROTL(A, 12)
        TT1 = (FF(A, B_, C, j) + D + SS2 + W1[j]) & 0xFFFFFFFF
        TT2 = (GG(E, F, G, j) + H + SS1 + W[j]) & 0xFFFFFFFF

        D = C
        C = ROTL(B_, 9)
        B_ = A
        A = TT1
        H = G
        G = ROTL(F, 19)
        F = E
        E = P0(TT2)


    V[0] ^= A
    V[1] ^= B_
    V[2] ^= C
    V[3] ^= D
    V[4] ^= E
    V[5] ^= F
    V[6] ^= G
    V[7] ^= H

# SM3 哈希
def sm3_hash(message_bytes):
    len_bytes = len(message_bytes)
    bit_len = len_bytes * 8

    # 1. 填充
    padding = b'\x80'
    padding += b'\x00' * ((64 - (len_bytes + 1 + 8) % 64) % 64)
    padding += struct.pack(">Q", bit_len)  # Append length as big-endian 64-bit integer
    padded_message = message_bytes + padding
    # 2. 初始化
    V = IV[:]

    # 3. 迭代压缩
    for i in range(0, len(padded_message), 64):
        B = padded_message[i:i+64]
        sm3_compress(V, B)

    # 4. 输出 (转换为 32 字节的十六进制字符串)
    hash_bytes = b""
    for v in V:
        hash_bytes += struct.pack(">I", v)
    return hash_bytes

def print_hash(hash_bytes):
    for byte in hash_bytes:
        print(f"{byte:02x}", end="")
    print()

# -------------------   Main  -------------------
def main():
    base = "abcdefgh"  # C++ 中使用的 base 字符串
    num_blocks = 8

    # 构建输入消息，模拟 C++ 的方式
    message = bytearray()
    for i in range(num_blocks):
       block = bytearray()
       block.extend(base[i].encode('utf-8'))
       block.extend(b'\x00' * 63) #fill with zeros
       block[1] = 0x80
       block[63] = 8  # Length of "a" in bits. (i.e., the length of each char)
       message.extend(block)


    hash_result = sm3_hash(bytes(message))
    print("SM3 Hash: ", end="")
    print_hash(hash_result)


if __name__ == "__main__":
    main()
