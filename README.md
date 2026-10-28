# FKey Mapper - F键自定义工具

将键盘 F1-F12 映射为任意组合键或操作序列，支持多步骤编排和延迟控制。

## 功能特性

- **全局热键拦截** - 捕获 F1-F12 按键，执行自定义操作
- **操作序列编排** - 每个 F 键可配置多步操作，按顺序执行
- **四种操作类型**：
  - 组合键（如 Ctrl+C、Alt+F4）
  - 单键（如 Enter、Tab、Escape）
  - 文本输入（自动打字一段文字）
  - 延迟（等待指定毫秒数）
- **按键录制** - 按下组合键自动录入，也支持手动输入和常用预设
- **配置管理** - 自动保存、导入/导出 JSON 配置
- **测试执行** - 不通过 F 键触发，直接测试操作序列

## 系统要求

- Windows 7/8/10/11
- Python 3.8+（运行源码或打包时需要）
- 管理员权限（拦截全局键盘事件必需）

## 快速开始

### 直接运行（需要 Python 环境）

```bash
# 安装依赖
pip install -r requirements.txt

# 启动程序（会自动请求管理员权限）
python main.py
```

### 打包成独立 exe

```bash
# Windows 上直接双击
build.bat

# 或手动执行
pip install -r requirements.txt
pip install pyinstaller
pyinstaller --onefile --windowed --uac-admin --hidden-import keyboard --name FKeyMapper main.py
```

打包完成后在 `dist/FKeyMapper.exe` 就是最终程序，双击即可运行。

## 使用说明

### 基本操作

1. 启动程序后，左侧列表显示 F1-F12
2. 点击选中某个 F 键（如 F1）
3. 点击右侧按钮添加操作：
   - **组合键** - 按下想要的组合键自动录入，或从预设选择
   - **单键** - 从下拉列表选择或手动输入
   - **文本** - 输入要自动打字的内容
   - **延迟** - 输入等待时间（毫秒），提供快捷按钮
4. 可拖动调整操作顺序，或删除不需要的步骤
5. 点击「保存」保存配置

### 示例配置

**F1 = 复制 → 等待1秒 → 按回车**

```
操作1: 组合键 Ctrl+C
操作2: 延迟 1000 ms
操作3: 单键 Enter
```

**F2 = 粘贴**

```
操作1: 组合键 Ctrl+V
```

**F3 = 输入邮箱并回车**

```
操作1: 文本 "example@email.com"
操作2: 单键 Enter
```

### 配置文件

配置自动保存在程序同目录的 `fkey_config.json`，格式示例：

```json
{
  "F1": [
    {"type": "hotkey", "keys": ["ctrl", "c"]},
    {"type": "delay", "ms": 1000},
    {"type": "key", "key": "enter"}
  ],
  "F2": [
    {"type": "hotkey", "keys": ["ctrl", "v"]}
  ],
  "F3": [],
  "F4": [],
  "F5": [],
  "F6": [],
  "F7": [],
  "F8": [],
  "F9": [],
  "F10": [],
  "F11": [],
  "F12": []
}
```

支持导入/导出配置，方便备份和迁移。

## 注意事项

- 程序必须以管理员身份运行才能拦截全局键盘事件
- 被映射的 F 键会拦截原始功能（如 F1 帮助），可通过「启用拦截」开关临时禁用
- 同一时间只有一个操作序列在执行，快速连按不会重复触发
- 配置文件路径：程序同目录下的 `fkey_config.json`

## 技术栈

- Python 3.8+
- `keyboard` - 全局键盘钩子
- `tkinter` - GUI 界面
- `PyInstaller` - 打包成 exe

## 许可证

MIT License
