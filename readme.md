py-ubx
===

    wangXi <iwisunny@gmail.com>

# 1.Install
py-ubx集成到windows系统服务(services.msc)，请以管理员运行`install.bat`， 该脚本会自动处理依赖的python包
  
# 2.Cli
    ubx status  检查服务运行状态
    ubx install 安装服务到windows系统
    ubx auto  	安装服务到windows并开机自启动
    ubx start 	启动服务
    ubx stop  	停止服务
    ubx remove 	卸载服务
    
    ubx -s [cmd]    同步相关命令
    ubx -m [cmd]    监控相关命令
    
# 3.Troubleshooting
`ubx --log`     查看服务日志  
`ubx -s log`    查看同步日志  
`ubx -m log`    查看监控日志  

如果命令行提示错误 或服务启动异常，请打开`windows事件查看器`  
打开运行窗口(win+R)-->输入 `eventvwr` 检查application对应的的报错信息  
  
以上都无法解决问题，请联系开发者 `iwisunny@gmail.com`
