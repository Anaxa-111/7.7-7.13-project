# 实验2报告

## 原理

### 离散余弦变换（DCT）

离散余弦变换是一种重要的正交变换，能够将图像从空间域转换到频域，实现能量的集中化分布。

#### 二维DCT变换公式

对于大小为 $M \times N$ 的图像块 $f(x, y)$，其二维DCT变换定义为：

$$F(u, v) = \alpha(u) \alpha(v) \sum_{x=0}^{M-1} \sum_{y=0}^{N-1} f(x, y) \cdot \cos\left[ \frac{\pi (2x + 1)u}{2M} \right] \cdot \cos\left[ \frac{\pi (2y + 1)v}{2N} \right]$$

其中归一化因子为：

$$\alpha(u) = 
\begin{cases}
\sqrt{\frac{1}{M}}, & u = 0 \\
\sqrt{\frac{2}{M}}, & u > 0
\end{cases},
\quad
\alpha(v) = 
\begin{cases}
\sqrt{\frac{1}{N}}, & v = 0 \\
\sqrt{\frac{2}{N}}, & v > 0
\end{cases}$$

#### 逆DCT变换

相应的逆变换公式为：

$$f(x, y) = \sum_{u=0}^{M-1} \sum_{v=0}^{N-1} \alpha(u) \alpha(v) F(u, v) \cdot \cos\left[ \frac{\pi (2x + 1)u}{2M} \right] \cdot \cos\left[ \frac{\pi (2y + 1)v}{2N} \right]$$


## 水印算法

###  1.水印嵌入算法

####  算法流程

水印嵌入过程可以表示为以下数学模型：

设载体图像为 $I$，水印图像为 $W$，密钥为 $k$，则水印嵌入过程为：

$$I' = \text{Embed}(I, W, k)$$

具体步骤如下：

1. **图像预处理**：
   - 将载体图像 $I$ 分割成 $8 \times 8$ 块：$\{B_1, B_2, ..., B_n\}$
   - 排除边界区域，避免边界效应

2. **水印预处理**：
   - 将水印 $W$ 二值化：$W(i,j) \in \{0, 255\}$
   - 转换为嵌入标志：$w_{ij} = \begin{cases} 1 & W(i,j) = 255 \\ 0 & W(i,j) = 0 \end{cases}$

3. **伪随机块选择**：
   使用线性同余生成器产生伪随机序列：
   $$r_{n+1} = (a \cdot r_n + c) \bmod m$$
   其中 $r_0 = k$（密钥作为种子）

4. **DCT变换与系数修改**：
   对选定的图像块 $B_i$，计算其DCT变换：
   $$D_i = \text{DCT}(B_i)$$
   
   提取DC系数并量化：
   $$dc = \frac{D_i(0,0)}{\text{fact}}$$
   
   根据水印位修改DC系数：
   $$dc' = \begin{cases}
   \lceil dc \rceil \text{ if } \lceil dc \rceil \text{ is odd} & \text{when } w = 1 \\
   \lceil dc \rceil - 1 \text{ if } \lceil dc \rceil \text{ is even} & \text{when } w = 1 \\
   \lceil dc \rceil \text{ if } \lceil dc \rceil \text{ is even} & \text{when } w = 0 \\
   \lceil dc \rceil - 1 \text{ if } \lceil dc \rceil \text{ is odd} & \text{when } w = 0
   \end{cases}$$

5. **逆变换重构**：
   $$D_i'(0,0) = dc' \times \text{fact}$$
   $$B_i' = \text{IDCT}(D_i')$$

#### 冗余嵌入策略

为增强鲁棒性，对每个水印位采用冗余嵌入：

$$\forall w_{ij}, \exists \{B_{k_1}, B_{k_2}, ..., B_{k_r}\} \text{ s.t. } \text{每个块都嵌入} w_{ij}$$

其中 $r$ 为冗余因子。

### 2.水印提取算法

#### 提取流程

水印提取过程为嵌入的逆过程：

$$W' = \text{Extract}(I', k)$$

1. **图像分块**：使用相同的分块策略

2. **伪随机序列重现**：使用相同密钥 $k$ 生成相同的随机序列

3. **DC系数提取与判决**：
   对每个相关块 $B_i'$：
   $$dc_{extracted} = \frac{\text{DCT}(B_i')(0,0)}{\text{fact}}$$
   
   奇偶性判决：
   $$w'_{ij} = \begin{cases}
   1 & \text{if } \lfloor dc_{extracted} + 0.5 \rfloor \text{ is odd} \\
   0 & \text{if } \lfloor dc_{extracted} + 0.5 \rfloor \text{ is even}
   \end{cases}$$

4. **投票机制**：
   对于冗余嵌入的情况，采用多数投票：
   $$w^{\prime}_{ij} = \operatorname{MajorityVote}\!\left( \{ w^{\prime (1)}_{ij}, w^{\prime (2)}_{ij}, \ldots, w^{\prime (r)}_{ij} \} \right)$$



##  鲁棒性分析

### 几何攻击

1. **缩放攻击**：DC系数在缩放操作下相对稳定，但需要在提取时进行尺寸归一化
2. **裁剪攻击**：边界切除策略提供了一定的裁剪容忍度
3. **旋转攻击**：由于使用固定的8×8分块，对旋转攻击敏感

### 信号处理攻击

1. **滤波攻击**：DC系数作为低频分量，对低通滤波具有一定抗性
2. **噪声攻击**：量化因子提供了噪声容忍度
3. **压缩攻击**：JPEG压缩也使用DCT，因此具有一定的压缩抗性

### 数学分析

设噪声为 $n(x,y)$，受攻击图像为：
$$I''(x,y) = I'(x,y) + n(x,y)$$

相应的DC系数变化为：
$$dc'' = dc' + \frac{1}{64}\sum_{x=0}^{7}\sum_{y=0}^{7}n(x,y)$$

当 $|dc'' - dc'| < \text{fact}/2$ 时，水印可以正确提取。

## 实验结果

