import struct

# 常量定义
IV = [
    0x7380166f, 0x4914b2b9, 0x172442d7, 0xda8a0600,
    0xa96f30bc, 0x163138aa, 0xe38dee4d, 0xb0fb0e4e
]

T_j = [
    0x79cc4519,  # 0 <= j <= 15
    0x7a879d8a   # 16 <= j <= 63
]


# 循环左移函数
def ROTL(x, n):
    """循环左移"""
    return ((x << n) & 0xFFFFFFFF) | ((x & 0xFFFFFFFF) >> (32 - n))


# 布尔函数 FF
def FF0(x, y, z):
    """布尔函数 FF0 (0 <= j <= 15)"""
    return x ^ y ^ z


def FF1(x, y, z):
    """布尔函数 FF1 (16 <= j <= 63)"""
    return (x & y) | (x & z) | (y & z)


# 布尔函数 GG
def GG0(x, y, z):
    """布尔函数 GG0 (0 <= j <= 15)"""
    return x ^ y ^ z


def GG1(x, y, z):
    """布尔函数 GG1 (16 <= j <= 63)"""
    return (x & y) | (~x & z)


# 置换函数 P
def P0(x):
    """置换函数 P0"""
    return x ^ ROTL(x, 9) ^ ROTL(x, 17)


def P1(x):
    """置换函数 P1"""
    return x ^ ROTL(x, 15) ^ ROTL(x, 23)


# 消息扩展函数
def msg_extension(B):
    """
    消息扩展
    输入：512比特的消息分组B (64字节)
    输出：W[0..67] 和 W_prime[0..63]
    """
    W = [0] * 68
    W_prime = [0] * 64

    # 将B拆分成16个32比特字W[0..15]
    for i in range(16):
        W[i] = struct.unpack('>I', B[i * 4:(i + 1) * 4])[0]

    # 扩展W[16..67]
    for j in range(16, 68):
        W[j] = P1(W[j - 16] ^ W[j - 9] ^ ROTL(W[j - 3], 15)) ^ ROTL(W[j - 13], 7) ^ W[j - 6]

    # 计算W_prime[0..63]
    for j in range(64):
        W_prime[j] = W[j] ^ W[j + 4]

    return W, W_prime


# 压缩函数
def sm3_compress(V, B):
    """
    SM3 压缩函数
    输入：256比特的链接变量V (8个32比特字)，512比特的消息分组B (64字节)
    输出：更新后的链接变量V
    """
    A, B, C, D, E, F, G, H = V[:]  # 复制当前链接变量

    W, W_prime = msg_extension(B)

    for j in range(64):
        SS1 = ROTL((ROTL(A, 12) + E + ROTL(T_j[0] if j <= 15 else T_j[1], j)) & 0xFFFFFFFF, 7)
        SS2 = SS1 ^ ROTL(A, 12)

        TT1 = 0
        TT2 = 0

        if 0 <= j <= 15:
            TT1 = (FF0(A, B, C) + D + SS2 + W_prime[j]) & 0xFFFFFFFF
            TT2 = (GG0(E, F, G) + H + SS1 + W[j]) & 0xFFFFFFFF
        else:  # 16 <= j <= 63
            TT1 = (FF1(A, B, C) + D + SS2 + W_prime[j]) & 0xFFFFFFFF
            TT2 = (GG1(E, F, G) + H + SS1 + W[j]) & 0xFFFFFFFF

        D = C
        C = ROTL(B, 9)
        B = A
        A = TT1
        H = G
        G = ROTL(F, 19)
        F = E
        E = TT2

    # 将结果加到原V上 (按位异或)
    V[0] = (A ^ V[0]) & 0xFFFFFFFF
    V[1] = (B ^ V[1]) & 0xFFFFFFFF
    V[2] = (C ^ V[2]) & 0xFFFFFFFF
    V[3] = (D ^ V[3]) & 0xFFFFFFFF
    V[4] = (E ^ V[4]) & 0xFFFFFFFF
    V[5] = (F ^ V[5]) & 0xFFFFFFFF
    V[6] = (G ^ V[6]) & 0xFFFFFFFF
    V[7] = (H ^ V[7]) & 0xFFFFFFFF


# SM3 主哈希函数
def sm3_hash(message: bytes) -> bytearray:
    """
    SM3 哈希函数
    输入：消息字节串
    输出：32字节的哈希值
    """
    msg_len = len(message)  # 获取消息字节长度
    bit_len = msg_len * 8  # 消息比特长度

    # 消息填充
    # 1. 添加一个 0x80 (10000000b)
    # 2. 添加 k 个 0x00，使得填充后的总长度为 448 mod 512
    # 3. 添加 64 位的消息长度 (以比特为单位)
    padded_len = 64 * ((msg_len + 8 + 1 + 63) // 64)  # 计算填充后的总长度，必须是64字节的倍数
    padded = bytearray(padded_len)
    padded[:msg_len] = message  # 复制原始消息
    padded[msg_len] = 0x80  # 添加 '1' 比特 (0x80)
    #  填充0
    for i in range(msg_len + 1, padded_len - 8):
        padded[i] = 0x00
    # 添加 64 位消息长度 (大端)
    for i in range(8):
        padded[padded_len - 8 + i] = (bit_len >> (8 * (7 - i))) & 0xFF

    # 初始化链接变量 V
    V = IV[:]  # 复制初始向量

    # 迭代压缩
    for i in range(0, padded_len, 64):
        sm3_compress(V, padded[i:i + 64])

    # 将最终的链接变量转换为字节串
    digest = bytearray(32)
    for i in range(8):
        digest[4 * i:4 * i + 4] = struct.pack('>I', V[i])
    return digest


if __name__ == '__main__':
    input_str = "123456789"
    print(f"Input= {input_str}")
    hash_result = sm3_hash(input_str.encode('utf-8'))
    print("Result= ", end="")
    for byte in hash_result:
        print(f"{byte:02x}", end="")
    print()

    input_str_test = "abc"
    print(f"\nInput= {input_str_test}")
    hash_result_test = sm3_hash(input_str_test.encode('utf-8'))
    print("Result= ", end="")
    for byte in hash_result_test:
        print(f"{byte:02x}", end="")
    print(" ")

    input_str_empty = ""
    print(f"\nInput= '{input_str_empty}' (empty string)")
    hash_result_empty = sm3_hash(input_str_empty.encode('utf-8'))
    print("Result= ", end="")
    for byte in hash_result_empty:
        print(f"{byte:02x}", end="")
    print(" ")
