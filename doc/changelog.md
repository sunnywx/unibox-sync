ChangeLog
===

## v1.2.5
- 增加日志清理机制，仅保留最近一星期的日志
- python ConfigParser 写入的时候换行符没有清理，默认为unibox的LF，统一转换为CRLF
- 增加自动更新模块

## v1.2.6-a
- sqlite 本地结构变更，参考`migration` 目录

## 2016-5-6
- urllib2 urlopen Errno10060, [http://stackoverflow.com/questions/2923703/why-cant-i-get-pythons-urlopen-method-to-work-on-windows]  
try multiple times when use urllib2 to open remote, and set http connection Keep-Alive