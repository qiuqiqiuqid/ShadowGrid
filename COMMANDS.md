# ShadowGrid 命令文档

## 基本命令

### ls / dir

列出目录内容。

用法：
```
ls [路径]
```

示例：
```
ls                    # 列出当前目录
ls /etc              # 列出/etc目录
ls C:/Users          # 列出Windows用户目录
```

输出格式：
- 目录以 `/` 结尾
- 文件正常显示

### cd

切换目录。

用法：
```
cd <目录>
```

示例：
```
cd /tmp
cd Documents
cd ..
```

### pwd

显示当前工作目录。

用法：
```
pwd
```

示例：
```
pwd
```

### cat

显示文件内容。

用法：
```
cat <文件>
```

示例：
```
cat /etc/passwd
cat config.json
cat script.py
```

### dl

下载文件。

用法：
```
dl <文件> [目录]
```

示例：
```
dl logfile.txt              # 下载到默认下载目录
dl /etc/passwd /tmp        # 下载到/tmp目录
dl secret.txt downloads/   # 下载到downloads目录
```

### ud

上传文件。

用法：
```
ud <本地文件> [远程目录]
```

示例：
```
ud myscript.py
ud myscript.py /tmp
ud config.json .
```

### rm

删除文件或目录。

用法：
```
rm <路径> [-r]
```

示例：
```
rm temp.txt              # 删除文件
rm /tmp/cache -r        # 递归删除目录
rm test/old -r          # 删除旧目录
```

### mv

移动或重命名文件/目录。

用法：
```
mv <源> <目标>
```

示例：
```
mv old.txt new.txt       # 重命名
mv file.txt /tmp         # 移动到/tmp
mv demo/old demo/new    # 移动并重命名
```

### file

查看文件类型。

用法：
```
file <路径>
```

示例：
```
file script.py          # 显示: text
file image.jpg          # 显示: image
file archive.zip        # 显示: archive
```

支持的文件类型：
- text：文本文件（.txt, .md, .json等）
- executable：可执行文件（.exe, .bat等）
- image：图片文件（.jpg, .png等）
- pdf：PDF文件
- audio：音频文件
- video：视频文件
- archive：压缩文件（.zip, .tar等）
- directory：目录
- shortcut：快捷方式

### find

查找文件。

用法：
```
find <模式> [-t <类型>]
```

参数：
- `<模式>`：文件名匹配模式
- `-t`：文件类型过滤（f=文件, d=目录）

示例：
```
find .py               # 查找所有.py文件
find password -t f     # 查找名为password的文件
find test -t d         # 查找名为test的目录
find log -t f         # 查找所有包含log的文件
```

示例输出：
```
  [FILE] /var/log/syslog
  [DIR] /tmp/test
  [FILE] /home/user/test.py
```

## 高级命令

### screenshot

截取远程屏幕。

用法：
```
screenshot
```

示例：
```
screenshot
```

结果：
截图保存在 `screenshots/` 目录，文件名格式：`{client_id}_shot.png`

### echo

回显文本。

用法：
```
echo <文本>
```

示例：
```
echo Hello ShadowGrid
echo Test message
```

### time

获取远程时间。

用法：
```
time
```

示例：
```
time
```

### test

测试连接。

用法：
```
test
```

示例：
```
test
```

## 通用命令

### help

显示帮助信息。

用法：
```
help
```

### list

列出所有连接的设备。

用法：
```
list
```

### use

选择设备。

用法：
```
use <编号>
```

示例：
```
use 1    # 选择第一个设备
use 3    # 选择第三个设备
```

### back

返回设备列表。

用法：
```
back
```

### clear

清屏。

用法：
```
clear
```

### quit

退出程序。

用法：
```
quit
```

## 交互模式

选择设备后，可以直接使用上述命令：

```
srt > use 1
[信息] 已连接到设备: DESKTOP-XXX (ID: abc12345)
desktop:~ > ls
desktop:~ > cd Documents
desktop:Documents > cat file.txt
desktop:Documents > dl file.txt
desktop:Documents > back
```

## 错误处理

常见错误：

1. **无效路径**：路径超出允许范围或不存在
2. **文件未找到**：指定的文件或目录不存在
3. **权限拒绝**：没有足够的权限访问资源
4. **类型错误**：`-t` 参数必须是 `f` 或 `d`

## 客户端命令

客户端支持的命令类型：

| 命令 | 说明 |
|------|------|
| test | 测试连接 |
| echo | 回显 |
| time | 时间 |
| screenshot | 截图 |
| ls | 列表 |
| cat | 查看文件 |
| dl | 下载 |
| ud | 上传 |
| cd | 切换目录 |
| pwd | 当前目录 |
| rm | 删除 |
| mv | 移动 |
| file | 文件类型 |
| find | 查找 |

## 示例场景

### 场景1：文件传输
```
use 1
cd /var/log
dl syslog /tmp/
dl auth.log /tmp/
```

### 场景2：远程调查
```
use 2
ls
find .py -t f
find secret -t f
cat config.json
```

### 场景3：系统清理
```
use 3
cd /tmp
find cache -t d
rm cache_dir -r
find .tmp -t f
rm temp.tmp
```
