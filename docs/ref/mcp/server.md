### 基本使用指南  
要初始化 `my_app` 配置框架，请从主模块调用 `initialize()` 函数：  
```python  
from my_app import core  
core.initialize()  
```

#### 配置层级  
该框架支持 **环境感知配置**：  
1.