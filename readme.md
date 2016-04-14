py-ubx
===

## a sync and monitor tool built with python 
    <iwisunny@gmail.com>

# 1.install
py-ubx集成到windows服务(services.msc)，首次安装请以管理员运行`install.bat`
  
# 2.cli
    ubx install 安装服务
    ubx auto  	安装服务,开机自启动
    ubx status  检查服务状态
    ubx start 	启动服务
    ubx stop  	停止服务
    ubx reload  重启服务
    ubx remove 	卸载服务    
    ubx -s [cmd]    同步相关指令
    ubx -m [cmd]    监控相关指令
    ubx --log       查看程序日志
    
# 3.deploy
每次发布新的tag, 修改unibox.ini的version到最新的版本号，如果是数据表要更改，
请根据当前version添加 `migration`  
如果表数据要作大规模调整，比如修改movie的一列数据，请在migration中删除表数据， 
以便下次同步完整数据

若命令行报错，请先查看对应日志，并结合windows事件查看器(`eventvwr`)排错

# 4.user_guide
### 【前言】
py-ubx是unibox同步与监控程序的代号，以下统称ubx。  
ubx是unibox分布式系统的客户端程序，作为租赁程序的服务支持层。  
ubx提供租赁机终端数据同步，机器监控，为监控系统web端提供数据支持。  

ubx由python编写，设计架构是创建一个称为 UniboxSvc 的windows系统服务，  
UniboxSvc管理 sync进程(同步作业) 和 monitor进程(监控作业)。


### 【申明】
为了保证出厂机器的部署规范，后期维护的方便，减小机器软件故障率，特编写此文档。  
请部署人员务必认真阅读此文档，严格参照执行，如果参照执行，程序出了问题，那是开发人员的  
职责，如果不参照此文档，程序部署错误，后果由部署人员负责，特此申明。  


### 【监控异常说明】
定义异常的机器，依据此说明来判别机器是否出现监控异常：

在浏览器上打开监控web页 http://monitor.unibox.com.cn，查看各机器的监控状况，
#### 【以下情况视为监控异常，需要部署人员手动安装ubx程序】
    (1) [今日流量] 这一列 下载/上传 流量超过500MB，即为流量异常  
    (2) [ubx版本] 这一列 为空白 或者低于当前最新版本，  
   获取当前最新版本号，请打开 http://pub.unibox.com.cn/update.txt

如果出现 **(1)(2)** 中的任何一种情况，说明ubx已经部署异常，无法自我升级修复，  
需要跳到 **【详细步骤】** ，根据步骤手动安装ubx，否则机器ubx部署正常，无需其它操作。  


### 【详细步骤】
1. ubx程序统一安装在 C:\py-ubx目录下，请严格遵守此目录，不要随意更改目录名。  

2. 从http://pub.unibox.com.cn下载最新版本的py-ubx程序包, 最新版本号依据 http://pub.unibox.com.cn/update.txt  
将下载的 py-ubx-v***.zip 解压到C盘根目录，重命名目录为py-ubx，目录结构（核心文件和目录）如下:
    
    C:\py-ubx  
        |-apps  
        |-lib  
        |-migration  
        |-cli.bat  
        |-install.bat  
        |-svc.py  
        |-ubx.py  
        |-unibox.ini  
        |-requirements.txt  

3. 进入c:\py-ubx目录，双击install.bat，如果提示权限不够，请右键->以管理员运行，  
 程序会自动编译py-ubx的可执行文件，编译完成后窗口自动关闭。  

4. 打开浏览器，定位到 http://monitor.unibox.com.cn，看到刚刚部署的机器在监控页正常显示，则部署成功，安装到此结束。  


### 【错误修复】
如果http://monitor.unibox.com.cn页面显示 机器依然断开，则ubx可能安装失败，请参考以下排错：  

- 双击cli.bat, 输入 ubx status，如果提示[svc] running 则服务正在运行， [svc] stopped，则服务已停止。
- 输入 ubx --log 查看ubx的日志文件，请将日志保存，或者截图 通知开发者(wangxi@unibox.com.cn)
- 如果命令行输入直接报错，则有可能是python环境破坏了，此时需要重装（修复）python环境

### 【python环境修复】
1. 打开windows程序列表（win+R键调出运行框，输入 appwiz.cpl），定位到python，右键点击 repair(修复)  
    如果一切正常（未提示错误弹框），跟着python安装提示一步步走，待环境安装完成。完成后打开cmd窗口，输入pip --version，  
    如果屏幕打印出版本号，没有报错信息，则python环境修复成功，之后再参考【详细步骤】安装ubx程序。  

2. 如果在程序列表中，右键修复python提示 [A program required for this install to complete could not be run] 的提示,  
    则可能是当前用户对Temp目录没有写权限，此时的修复 比较复杂，以下说明仅作参考，如果觉得不会操作，可以记下机器编号，联系开发者：  
    1) win+R调出运行框，输入%localAppData% 打开当前登录用户的【应用数据目录】，找到Temp目录  
    2) 右键点击 Temp -> 点击 【属性】 (Property)， -> 点击 【安全】(Security)选项卡  
    3) 点击 编辑(Edit) 按钮，弹出Temp目录的权限对话框，-> 点击 添加(Add)按钮，弹出 选择用户和组 对话框  
    4) 点击 高级(Advanced)按钮，再点击 立即查找 按钮，在下方搜索结果中选中 Everyone ，点击 确定  
    5) 回到 Temp权限对话框，在 [组和用户名] 窗口，选中Everyone ，下方 [Everyone的权限] 将 完全控制(Full acess) 勾选  
    6）点击 应用，确定按钮，退出 Temp权限对话框，再按照【python环境的重装修复】[1]的方式 重新安装python环境，之后安装ubx  


