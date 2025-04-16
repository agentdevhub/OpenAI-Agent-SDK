# 测试

在运行任何测试之前，请确保已安装 `uv`（建议随后运行 `make sync`）。

## 运行测试

```
make tests
```

## 快照测试

我们使用 [inline-snapshots](https://15r10nk.github.io/inline-snapshot/latest/) 进行部分测试。若您的代码新增了快照测试或导致现有测试失败，可执行以下操作修复/创建快照。完成快照修复/创建后，请重新运行 `make tests` 以验证测试是否通过。

### 修复快照

```
make snapshots-fix
```

### 创建快照

```
make snapshots-update
```