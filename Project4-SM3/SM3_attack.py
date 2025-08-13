import struct

def ROTL(x, n):
    return ((x << n) | (x >> (32 - n))) & 0xFFFFFFFF  # 确保在 32 位内

def FF0(x, y, z):
    return x ^ y ^ z

def FF1(x, y, z):
    return (x & y) | (x & z) | (y & z)

def GG0(x, y, z):
    return x ^ y ^ z

def GG1(x, y, z):
    return (x & y) | (~x & z) & 0xFFFFFFFF   # 确保结果在 32 位内

def P0(x):
    return x ^ ROTL(x, 9) ^ ROTL(x, 17)

def P1(x):
    return x ^ ROTL(x, 15) ^ ROTL(x, 23)

IV = [
    0x7380166f, 0x4914b2b9, 0x172442d7, 0xda8a0600,
    0xa96f30bc, 0x163138aa, 0xe38dee4d, 0xb0fb0e4e
]

T_j = [
    0x79cc4519] * 16 + [0x7a879d8a] * 48


def sm3_compress(V, B):
    W = [0] * 68
    W1 = [0] * 64

    for i in range(16):
        W[i] = (B[4*i] << 24) | (B[4*i+1] << 16) | (B[4*i+2] << 8) | B[4*i+3]

    for i in range(16, 68):
        W[i] = P1(W[i-16] ^ W[i-9] ^ ROTL(W[i-3], 15)) ^ ROTL(W[i-13], 7) ^ W[i-6]
        W[i] = W[i] & 0xFFFFFFFF  # 确保在 32 位内
    for i in range(64):
        W1[i] = W[i] ^ W[i+4]
        W1[i] = W1[i] & 0xFFFFFFFF  # 确保在 32 位内
    A, B_, C, D = V[0], V[1], V[2], V[3]
    E, F, G, H = V[4], V[5], V[6], V[7]

    for j in range(64):
        SS1 = ROTL(ROTL(A, 12) + E + ROTL(T_j[j], j % 32), 7) & 0xFFFFFFFF # 确保在 32 位内
        SS2 = SS1 ^ ROTL(A, 12)
        TT1 = (FF0(A, B_, C) if j < 16 else FF1(A, B_, C)) + D + SS2 + W1[j]
        TT1 = TT1 & 0xFFFFFFFF # 确保在 32 位内
        TT2 = ((GG0(E, F, G) if j < 16 else GG1(E, F, G)) + H + SS1 + W[j]) & 0xFFFFFFFF # 确保在 32 位内

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


def sm3_hash(message):
    message_bytes = message.encode('utf-8')
    len_bytes = len(message_bytes)
    bit_len = len_bytes * 8

    padding_len = 64 - ((len_bytes + 1 + 8) % 64)
    if padding_len == 64:
        padding_len = 0

    padding = b'\x80' + b'\x00' * padding_len
    padding += struct.pack(">Q", bit_len)   # 大端模式，8 字节整数
    padded_message = message_bytes + padding

    V = IV[:]  # 创建 IV 的副本，避免修改原始 IV
    for i in range(0, len(padded_message), 64):
        B = padded_message[i:i+64]
        sm3_compress(V, list(B))

    digest = b''
    for v in V:
        digest += struct.pack(">I", v)  # 大端模式，4 字节整数
    return digest


def sm3_hash_continue(extension, original_hash, original_total_len):
    # From original hash recover the internal state
    V = []
    for i in range(8):
        V.append(struct.unpack('>I', original_hash[i * 4:i * 4 + 4])[0])

    # Prepare data for the next compression round.
    original_padded_len = ((original_total_len + 1 + 8 + 63) // 64) * 64
    message_to_pad = extension
    total_bit_len = (original_padded_len + len(message_to_pad)) * 8

    padding_len = 64 - ((len(message_to_pad) + 1 + 8) % 64)
    if padding_len == 64:
       padding_len = 0
    padding = b'\x80' + b'\x00' * padding_len
    padding += struct.pack(">Q", total_bit_len)  # 大端模式, 8 字节整数

    padded_message = message_to_pad + padding
    for i in range(0, len(padded_message), 64):
         B = padded_message[i:i+64]
         sm3_compress(V, list(B))

    digest = b''
    for v in V:
        digest += struct.pack(">I", v)
    return digest


def print_hash(label, hash_bytes):
    print(label, end="")
    for byte in hash_bytes:
        print(f"{byte:02x}", end="")
    print()


# Main execution
if __name__ == "__main__":
    secret_key = "secret_key"  # Secret key (must be known when constructing the complete message)
    original_data = "plaintext"   # Original data
    extension_data = "faketext"  # Data the attacker wants to add

    # 1. Calculate original hash
    msg1 = secret_key + original_data
    original_hash = sm3_hash(msg1)

    # 2. Forge the hash
    ext_vec = extension_data
    forged_hash = sm3_hash_continue(ext_vec, original_hash, len(secret_key + original_data))

    # 3. Construct full message by the attacker
    original_len = len(secret_key + original_data)
    padded_len = ((original_len + 1 + 8 + 63) // 64) * 64
    padding_len = padded_len - original_len
    padding = b'\x80' + b'\x00' * (padding_len - 1) + struct.pack(">Q", original_len * 8) # Use correct padding
    # Use correct input for calculating  legitimate_hash
    msg2 = msg1+ padding.decode('latin-1') + extension_data
    legitimate_hash = sm3_hash(msg2)
    
    print_hash("Original hash:   ", original_hash)
    print_hash("Forged hash:     ", forged_hash)
    print_hash("Legitimate hash: ", legitimate_hash)

    if forged_hash == legitimate_hash:
        print("\nAttack successful, forged hash matches legitimate hash")
    else:
        print("\nAttack failed")
