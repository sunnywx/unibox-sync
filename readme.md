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
    
# 3.tips
若命令行报错，请先查看对应日志，并结合windows事件查看器(`eventvwr`)排错

# 4.deploy
每次发布新的tag, 修改unibox.ini的version到最新的版本号，如果是数据表要更改，
请根据当前version添加 `migration`  
如果表数据要作大规模调整，比如修改movie的一列数据，请在migration中删除表数据， 
以便下次同步完整数据

