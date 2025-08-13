import hashlib
import struct
import math

# 模拟 C++ 代码中的 ROTL， 需要处理负数左移，确保是 32 位
def ROTL(x, n):
    n = n % 32
    return ((x << n) | (x >> (32 - n))) & 0xFFFFFFFF

def FF0(x, y, z):
    return x ^ y ^ z

def FF1(x, y, z):
    return (x & y) | (x & z) | (y & z)

def GG0(x, y, z):
    return x ^ y ^ z

def GG1(x, y, z):
    return (x & y) | (~x & z) & 0xFFFFFFFF

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
        W[i] = W[i] & 0xFFFFFFFF  # 确保在 32 位内
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
        TT2 = (GG0(E, F, G) if j < 16 else GG1(E, F, G)) + H + SS1 + W[j]
        TT2 = TT2 & 0xFFFFFFFF
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

def sm3_hash(message_bytes):  # 接收字节字符串
    len_bytes = len(message_bytes)
    bit_len = len_bytes * 8

    padding_len = 64 - ((len_bytes + 1 + 8) % 64)
    if padding_len == 64:
        padding_len = 0

    padding = b'\x80' + b'\x00' * padding_len
    padding += struct.pack(">Q", bit_len)  # 大端模式，8 字节整数
    padded_message = message_bytes + padding

    V = IV[:]  # 创建 IV 的副本，避免修改原始 IV
    for i in range(0, len(padded_message), 64):
        B = padded_message[i:i+64]
        sm3_compress(V, list(B))

    digest = b''
    for v in V:
        digest += struct.pack(">I", v)  # 大端模式，4 字节整数
    return digest

def sm3_hash_str(message_str):
    return sm3_hash(message_str.encode('utf-8'))

def print_hash(label, hash_bytes):
    print(label, end="")
    for byte in hash_bytes:
        print(f"{byte:02x}", end="")
    print()
    
class MerkleTree:
    def __init__(self, leaves):
        self.leaves = leaves
        # 存储每层哈希值
        self.levels = []
        self.root = None
        self._build_tree()

    def hash_leaf(self, data):
        prefixed_data = b'\x00' + data
        return sm3_hash(prefixed_data)

    def hash_internal_node(self, left_hash, right_hash):
        prefixed_data = b'\x01' + left_hash + right_hash
        return sm3_hash(prefixed_data)

    def _build_tree(self):
        current_level = [self.hash_leaf(leaf) for leaf in self.leaves]
        self.levels.append(current_level)

        while len(current_level) > 1:
            next_level = []
            # 处理奇数个节点
            if len(current_level) % 2 != 0:
                current_level.append(current_level[-1])  # 复制最后一个节点
            for i in range(0, len(current_level), 2):
                left = current_level[i]
                right = current_level[i + 1]
                next_level.append(self.hash_internal_node(left, right))
            self.levels.append(next_level)
            current_level = next_level

        self.root = current_level[0] if current_level else b'' # 空树的根哈希


    def get_root(self):
        return self.root

    def generate_inclusion_proof(self, leaf_index):
        if leaf_index >= len(self.leaves):
            raise IndexError("Leaf index out of range.")
        proof = []
        current_index = leaf_index

        for level in self.levels[:-1]:
            sibling_index = current_index ^ 1  # XOR 技巧找到兄弟节点
            if sibling_index < len(level):
                proof.append(level[sibling_index])
            # 奇数层，最后一个哈希值是自己
            elif len(level) > 0:
                proof.append(level[current_index])
            current_index //= 2
        return proof

    @staticmethod
    def verify_inclusion_proof(leaf_data, leaf_index, proof, root_hash):
        if leaf_data is None or leaf_index is None or proof is None or root_hash is None:
            return False
        
        computed_hash =  sm3_hash(b'\x00' + leaf_data)

        for i, proof_hash in enumerate(proof):
            if leaf_index % 2 == 0:
                computed_hash = MerkleTree.hash_internal_node(computed_hash, proof_hash)
            else:
                computed_hash = MerkleTree.hash_internal_node(proof_hash, computed_hash)
            leaf_index //= 2
        return computed_hash == root_hash

    @staticmethod
    def hash_internal_node(left_hash, right_hash):
        prefixed_data = b'\x01' + left_hash + right_hash
        return sm3_hash(prefixed_data)
def main():

    # 生成叶子节点数据
    LEAF_COUNT = 100000
    leaves_data = []
    for i in range(LEAF_COUNT):
        leaf_str = "leaf-data-" + str(i)
        leaves_data.append(leaf_str.encode('utf-8'))  # 编码为字节串

    # 对叶子数据排序
    leaves_data.sort()

    # 构建 Merkle 树
    print("构建 Merkle 树：")
    tree = MerkleTree(leaves_data)
    root_hash = tree.get_root()
    print_hash("MT 构建完成，根哈希为: ", root_hash)

    # 4. 存在性证明 (Inclusion Proof)
    print("\n存在性证明：")
    target_leaf_str = "leaf-data-88888"
    target_leaf_data = target_leaf_str.encode('utf-8') # 目标叶子的数据，编码为字节串
    try:
        target_index = leaves_data.index(target_leaf_data)
        print("   目标叶子: \"", target_leaf_str, "\", 索引: ", target_index)
    except ValueError:
        print(f"   目标叶子 '{target_leaf_str}' 未找到。")
        exit()
    inclusion_proof = tree.generate_inclusion_proof(target_index)
    print("   生成的证明路径长度为: ", len(inclusion_proof), " 个哈希")

    is_valid_inclusion = MerkleTree.verify_inclusion_proof(target_leaf_data, target_index, inclusion_proof, root_hash)
    if is_valid_inclusion:
        print("存在性证明验证成功")
    else:
        print("存在性证明验证失败")


    # 不存在性证明 (Non-inclusion Proof)
    print("\n不存在性证明：")
    non_existent_leaf_str = "this-leaf-does-not-exist"
    non_existent_leaf_data = non_existent_leaf_str.encode('utf-8')

    # 使用 bisect_left 找到插入位置，该位置的前一个叶子节点的 Proof
    from bisect import bisect_left
    insert_index = bisect_left(leaves_data, non_existent_leaf_data)
    if insert_index == 0: # 不存在，并且比所有都小
        print ("不存在性证明失败:目标不存在，且是最小")
        exit()
    if insert_index == len(leaves_data): # 不存在，并且比所有都大
        proof_for_index = len(leaves_data) - 1
        proof_for_leaf_data = leaves_data[proof_for_index]
    else:
        proof_for_index = insert_index - 1
        proof_for_leaf_data = leaves_data[proof_for_index]

    proof_for_leaf_str = proof_for_leaf_data.decode('utf-8')
    print("通过证明叶子节点 \"", proof_for_leaf_str, "\", 索引 ", proof_for_index,"  的存在性")
    non_inclusion_proof = tree.generate_inclusion_proof(proof_for_index)
    is_valid_non_inclusion = MerkleTree.verify_inclusion_proof(proof_for_leaf_data, proof_for_index, non_inclusion_proof, root_hash)

    if is_valid_non_inclusion:
        print("不存在性证明验证成功")
    else:
        print("不存在性证明验证失败")
if __name__ == "__main__":
    main()
