py-ubx
===

## a sync and monitor tool built with python 
    <iwisunny@gmail.com>

# 1.Install
py-ubx集成到windows服务(services.msc)，首次安装请以管理员运行`install.bat`
  
# 2.Cli
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
    
# 3.Tips
若命令行报错，请先查看对应日志，并结合windows事件查看器(`eventvwr`)排错
