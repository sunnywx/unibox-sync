py-ubx
===

    wangXi <iwisunny@gmail.com>

# 1.Install
py-ubx集成到windows服务(services.msc)，首次安装请以管理员运行`install.bat`， 该脚本会自动处理依赖
  
# 2.Cli
    ubx install 安装py-ubx
    ubx status  检查服务状态
    ubx auto  	安装py-ubx,开机自启动
    ubx start 	启动服务
    ubx stop  	停止服务
    ubx remove 	卸载服务
    
    ubx -s [cmd]    同步相关命令
    ubx -m [cmd]    监控相关命令
    
# 3.Tips
`ubx --log`     py-ubx日志  
`ubx -s log`    同步日志  
`ubx -m log`    监控日志  

如果命令行提示错误 或服务启动异常，请打开`windows事件查看器`(打开运行窗口(win+R)-->输入 `eventvwr`)  
检查Application对应的的报错信息  
