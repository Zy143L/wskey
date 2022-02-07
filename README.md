## 新年快乐 恭喜发财

----

###  Python

### 新语法特性
```
PEP584，dict支持并集运算符
PEP585，标准集合中的类型提示泛型
PEP614，放宽了对修饰语的语法限制
```


### 新的内建特性

```PEP616，删除前缀和后缀的字符串方法```

### 新的标准库特性

```PEP593，增加了os.pidfd_open允许没有竞争和信号的过程管理```


### 编译器改进

```PEP573，从C扩展类型的方法快速访问模块状态
PEP617，CPython使用基于PEG的新解析器，
一些python内建函数（range，tuple，set，frozenset，list，dict）通过vetctorcall提速。vectorcall是PEP590的内容。垃圾回收不会阻塞新唤醒的对象。
一些模块（_abc,audioop,_bz2,_codecs;_contextvars,_crypt,_functools;_json,_loccale;math,operator,resource,time,_weakref）使用PEP489定义的多阶段初始化。
一些标准库模块（audioop,ast,grp,_hashlib,pwd,_posixubprocess,random,select,struct,termois,zlib）使用PEP384定义的稳定ABI。
```