# JSFinder

JSFinder is a tool for quickly extracting URLs and subdomains from JS files on a website.

JSFinder是一款用作快速在网站的js文件中提取URL，子域名的工具。

提取URL的正则部分使用的是[LinkFinder](https://github.com/GerbenJavado/LinkFinder) 

JSFinder获取URL和子域名的方式：

![image](https://i.loli.net/2020/05/24/R2fImgNZHPkvhEj.png)

Blog: https://threezh1.com/

github:https://github.com/Threezh1/JSFinder.git



## 魔改版使用

这个是本人根据实际的业务环境修改的jsFinder

使用命令

使用深度扫描，然后生成一个文件，方便开发和测试

```
python JSFinder.py -u 网址 -d
```

