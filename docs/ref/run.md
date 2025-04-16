# PyTorch 概述

PyTorch 是一个基于 Python 的科学计算框架，主要应用于两类场景：  
- 替代 NumPy 使用 GPU 的强大算力进行张量运算  
- 提供最大灵活性和速度的深度学习研究平台

## 核心特性
**动态计算图**：通过 autograd 模块实现即时构建和修改计算图（又称「define-by-run」模式）。  
```python
x = torch.tensor([1.0], requires_grad=True)
y = x**2 + 3  # 运算步骤被自动记录
```
**张量加速**：使用 CUDA 张量类型在 NVIDIA GPU 上实现并行计算加速：  
```python
if torch.cuda.is_available():
    tensor = tensor.to('cuda')  # 将张量迁移至 GPU
```
**模块化神经网络**：通过 `torch.nn` 模块提供可组合的神经网络层和损失函数：  
```python
loss_fn = nn.CrossEntropyLoss()
optimizer = torch.optim.SGD(model.parameters(), lr=0.01)
```